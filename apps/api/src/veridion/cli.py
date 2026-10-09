"""Command-line interface: `veridion <command>`.

    serve                 run the API (with the embedded worker unless disabled)
    worker                run a background worker process
    db init|upgrade|...   create tables (development) or manage Alembic migrations
    catalog validate|load check and load the requirement catalogue
    samples generate      render the fictional sample PDFs
    seed demo             create the demo organization with sample companies and runs
    demo snapshot         export the demo workspace as static JSON for the public demo
    eval run              run the evaluation suite
    admin set-plan        change an organization's plan
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
from datetime import date, timedelta
from pathlib import Path

from veridion.config import API_ROOT, REPO_ROOT, get_settings

SAMPLES_DIR = API_ROOT / "samples" / "pdfs"
DEMO_EMAIL = "demo@veridion.example"


def _logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)


def _migrate_to_head() -> None:
    """Apply migrations, holding a PostgreSQL advisory lock so concurrent instances wait their turn."""
    from alembic import command
    from sqlalchemy import text

    from veridion.db import MIGRATION_LOCK, get_engine

    engine = get_engine()
    if engine.dialect.name != "postgresql":
        command.upgrade(_alembic_config(), "head")
        return
    with engine.connect() as conn:
        conn.execute(text("SELECT pg_advisory_lock(:key)"), {"key": MIGRATION_LOCK})
        try:
            command.upgrade(_alembic_config(), "head")
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": MIGRATION_LOCK})
            conn.commit()


def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn

    settings = get_settings()
    if args.migrate:
        _logging()
        _migrate_to_head()
    # X-Forwarded-For is honoured only from the proxies listed in FORWARDED_ALLOW_IPS.
    uvicorn.run("veridion.main:app", host=args.host, port=args.port, reload=args.reload,
                workers=None if args.reload else (args.workers or settings.web_concurrency),
                proxy_headers=True, forwarded_allow_ips=settings.forwarded_allow_ips, log_level="info")


def cmd_worker(args: argparse.Namespace) -> None:
    import signal

    from veridion.db import create_all
    from veridion.jobs import worker_loop

    _logging()
    if not get_settings().is_production:
        create_all()
    stop = threading.Event()

    # SIGTERM (docker stop, Kubernetes) and Ctrl-C finish the current job, then exit.
    def _stop(signum: int, _frame: object) -> None:
        logging.getLogger("veridion.jobs").info("Received %s; stopping after the current job", signal.Signals(signum).name)
        stop.set()

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    worker_loop(stop, get_settings().worker_poll_seconds)


def _alembic_config():
    from alembic.config import Config

    cfg = Config(str(API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_ROOT / "migrations"))
    return cfg


def cmd_db(args: argparse.Namespace) -> None:
    from alembic import command

    from veridion.db import create_all

    cfg = _alembic_config()
    if args.action == "init":
        # Development shortcut: create tables from the models, then record them as fully
        # migrated so later `db upgrade` runs apply only newer migrations.
        create_all()
        command.stamp(cfg, "head")
        print("Tables created.")
    elif args.action == "upgrade":
        from sqlalchemy import inspect

        from veridion.db import get_engine

        tables = set(inspect(get_engine()).get_table_names())
        if "organizations" in tables and "alembic_version" not in tables:
            sys.exit("This database's tables were created directly from the models (by the development server), "
                     "so it has no migration history. Run `veridion db init` to record it as current, or upgrade "
                     "an empty database.")
        command.upgrade(cfg, args.revision or "head")
        print("Database upgraded.")
    elif args.action == "downgrade":
        if not args.revision:
            sys.exit("Give the target revision, e.g. `veridion db downgrade -1`.")
        command.downgrade(cfg, args.revision)
    elif args.action == "revision":
        if not args.message:
            sys.exit('Give a message, e.g. `veridion db revision -m "add company sector"`.')
        command.revision(cfg, message=args.message, autogenerate=True)
    elif args.action == "check":
        # Fails (non-zero exit) when the models have changes no migration covers.
        command.check(cfg)
        print("Models and migrations agree.")
    elif args.action == "current":
        command.current(cfg, verbose=True)


def cmd_catalog(args: argparse.Namespace) -> None:
    from veridion.catalog import discover, load_catalog, set_status
    from veridion.db import create_all, session_scope

    sets = discover()
    for s in sets:
        print(f"{s.id:32} {s.review_status:9} {set_status(s):10} {len(s.requirements)} requirements")
    if args.action == "load":
        create_all()
        with session_scope() as session:
            changed = load_catalog(session)
        print("Loaded:", ", ".join(changed) or "nothing new")


def cmd_samples(args: argparse.Namespace) -> None:
    from veridion.samples.generator import write_samples

    for path in write_samples(Path(args.out) if args.out else SAMPLES_DIR):
        print(path)


def _ensure_samples() -> None:
    from veridion.samples.content import ALDERMERE_AR_V2, COMPANIES

    needed = [d.slug for c in COMPANIES for d in c.documents] + [ALDERMERE_AR_V2.slug]
    if not all((SAMPLES_DIR / f"{slug}.pdf").exists() for slug in needed):
        from veridion.samples.generator import write_samples

        write_samples(SAMPLES_DIR)


def cmd_seed(args: argparse.Namespace) -> None:
    from sqlalchemy import delete, select

    from veridion.assessment.engine import create_run
    from veridion.catalog import load_catalog
    from veridion.db import create_all, session_scope
    from veridion.jobs import run_pending
    from veridion.llm import get_provider
    from veridion.models import (
        Action,
        AssessmentRun,
        Company,
        CompanyPeer,
        Finding,
        Membership,
        Organization,
        Review,
        User,
    )
    from veridion.samples.content import COMPANIES
    from veridion.security import hash_password
    from veridion.services.documents import create_document

    _logging()
    create_all()
    _ensure_samples()
    password = args.password or os.environ.get("DEMO_PASSWORD") or "veridion-demo"
    mode = args.mode
    if mode == "auto":
        mode = "hybrid" if get_provider() is not None else "rules"

    with session_scope() as s:
        load_catalog(s)
        existing = s.execute(select(Organization).where(Organization.slug == "demo")).scalar_one_or_none()
        if existing is not None:
            if not args.reset:
                print("Demo organization already exists. Use --reset to recreate it.")
                return
            # Database-level cascade removes companies, documents, passages, runs, findings and actions.
            s.execute(delete(Organization).where(Organization.id == existing.id))
            s.flush()
            s.expunge_all()
        org = Organization(name="Veridion Demo Workspace", slug="demo", plan="enterprise", is_demo=True)
        s.add(org)
        user = s.execute(select(User).where(User.email == DEMO_EMAIL)).scalar_one_or_none()
        if user is None:
            user = User(email=DEMO_EMAIL, name="Demo Analyst", password_hash=hash_password(password))
            s.add(user)
        else:
            user.password_hash = hash_password(password)
        s.flush()
        s.add(Membership(org_id=org.id, user_id=user.id, role="owner"))
        ids: dict[str, str] = {}
        for sample in COMPANIES:
            company = Company(org_id=org.id, name=sample.name, industry=sample.industry, country=sample.country,
                              size_band=sample.size_band, fiscal_year_end=sample.fiscal_year_end,
                              description=sample.description, is_sample=True, created_by=user.id)
            s.add(company)
            s.flush()
            ids[sample.slug] = company.id
            for doc in sample.documents:
                create_document(s, org_id=org.id, company=company, data=(SAMPLES_DIR / f"{doc.slug}.pdf").read_bytes(),
                                filename=f"{doc.slug}.pdf", title=doc.title, doc_type=doc.doc_type,
                                period_label=doc.period_label, published_on=date.fromisoformat(doc.published_on),
                                uploaded_by=user.id, is_sample=True)
        for peer in ("tessaline", "corvane"):
            s.add(CompanyPeer(company_id=ids["aldermere"], peer_id=ids[peer], org_id=org.id))
        org_id, user_id = org.id, user.id
    print("Processing sample documents…")
    run_pending()

    deadline = date.today() + timedelta(days=75)
    plan = [("aldermere", "gri-302-305-2016@1.0.0", mode, "Initial review against catalogue 1.0.0"),
            ("aldermere", "gri-302-305-2016@1.1.0", mode, "Re-assessment after catalogue update 1.1.0"),
            ("tessaline", "gri-302-305-2016@1.1.0", "rules", None),
            ("corvane", "gri-302-305-2016@1.1.0", "rules", None)]
    for slug, set_id, run_mode, label in plan:
        with session_scope() as s:
            company = s.get(Company, ids[slug])
            create_run(s, org_id=org_id, company=company, requirement_set_id=set_id, mode=run_mode,
                       period_label="FY2025", deadline=deadline if slug == "aldermere" else None, user_id=user_id,
                       label=label, enforce_quota=False)
        print(f"Assessing {slug} against {set_id} ({run_mode})…")
        run_pending()

    with session_scope() as s:
        latest = s.execute(select(AssessmentRun).where(AssessmentRun.company_id == ids["aldermere"])
                           .order_by(AssessmentRun.created_at.desc())).scalars().first()
        findings = {f.requirement_code: f for f in s.execute(
            select(Finding).where(Finding.run_id == latest.id)).scalars()}
        if "305-4" in findings:
            s.add(Review(org_id=org_id, finding_id=findings["305-4"].id, reviewer_id=user_id, reviewer_name="Demo Analyst",
                         decision="accept", previous_status=findings["305-4"].status,
                         note="Checked the intensity ratio against Table 4 and the production figure on page 2."))
        if "302-1" in findings:
            s.add(Review(org_id=org_id, finding_id=findings["302-1"].id, reviewer_id=user_id, reviewer_name="Demo Analyst",
                         decision="comment", previous_status=findings["302-1"].status,
                         note="Asked the finance team which energy figure was used for the SECR disclosure."))
        actions = s.execute(select(Action).where(Action.company_id == ids["aldermere"])).scalars().all()
        for a in actions:
            if a.gap_key.startswith("conflict:"):
                a.owner, a.due_date, a.status = "Head of Finance", date.today() + timedelta(days=21), "in_progress"
            elif a.requirement_code == "305-3" and a.gap_key == "value":
                a.owner, a.due_date = "Sustainability Manager", date.today() + timedelta(days=60)
            elif a.requirement_code == "305-2":
                a.owner = "Energy Manager"
    print(f"\nDemo ready. Sign in as {DEMO_EMAIL} / {password}")


def cmd_snapshot(args: argparse.Namespace) -> None:
    from veridion.demo_snapshot import export_snapshot

    _logging()
    out = Path(args.out) if args.out else REPO_ROOT / "apps" / "web" / "public" / "demo"
    password = args.password or os.environ.get("DEMO_PASSWORD") or "veridion-demo"
    stats = export_snapshot(out, DEMO_EMAIL, password)
    print(json.dumps(stats, indent=2))


def cmd_eval(args: argparse.Namespace) -> None:
    from veridion.eval.runner import main as eval_main

    _logging()
    eval_main(args)


def cmd_admin(args: argparse.Namespace) -> None:
    from sqlalchemy import select

    from veridion.db import session_scope
    from veridion.models import Organization
    from veridion.services.entitlements import PLANS

    if args.plan not in PLANS:
        sys.exit(f"Plan must be one of {', '.join(PLANS)}")
    with session_scope() as s:
        org = s.execute(select(Organization).where(
            (Organization.id == args.org) | (Organization.slug == args.org))).scalar_one_or_none()
        if org is None:
            sys.exit("Organization not found")
        org.plan = args.plan
        print(f"{org.name}: plan set to {args.plan}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="veridion", description="Veridion evidence intelligence platform")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("serve", help="Run the API server")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")),
                   help="Port (default: $PORT, or 8000)")
    p.add_argument("--reload", action="store_true")
    p.add_argument("--migrate", action="store_true",
                   help="Apply database migrations before serving (for hosts without a release step)")
    p.add_argument("--workers", type=int, help="Server processes (default: WEB_CONCURRENCY, or 1)")
    p.set_defaults(fn=cmd_serve)

    p = sub.add_parser("worker", help="Run a background worker")
    p.set_defaults(fn=cmd_worker)

    p = sub.add_parser("db", help="Database management")
    p.add_argument("action", choices=["init", "upgrade", "downgrade", "revision", "check", "current"])
    p.add_argument("revision", nargs="?", help="Target revision for upgrade/downgrade (default: head)")
    p.add_argument("-m", "--message", help="Message for a new revision")
    p.set_defaults(fn=cmd_db)

    p = sub.add_parser("catalog", help="Requirement catalogue")
    p.add_argument("action", choices=["validate", "load"])
    p.set_defaults(fn=cmd_catalog)

    p = sub.add_parser("samples", help="Fictional sample documents")
    p.add_argument("action", choices=["generate"])
    p.add_argument("--out")
    p.set_defaults(fn=cmd_samples)

    p = sub.add_parser("seed", help="Seed data")
    p.add_argument("what", choices=["demo"])
    p.add_argument("--mode", choices=["auto", "rules", "hybrid"], default="auto")
    p.add_argument("--password")
    p.add_argument("--reset", action="store_true")
    p.set_defaults(fn=cmd_seed)

    p = sub.add_parser("demo", help="Public demo")
    p.add_argument("action", choices=["snapshot"])
    p.add_argument("--out")
    p.add_argument("--password")
    p.set_defaults(fn=cmd_snapshot)

    p = sub.add_parser("eval", help="Evaluation suite")
    p.add_argument("action", choices=["run"])
    p.add_argument("--mode", choices=["rules", "hybrid", "both"], default="rules")
    p.add_argument("--limit", type=int, default=0, help="Limit the number of cases (0 = all)")
    p.add_argument("--out", help="Write the markdown report to this path")
    p.add_argument("--json", dest="json_out", help="Write raw results JSON to this path")
    p.add_argument("--web-summary", dest="web_summary", help="Write a compact metrics JSON for the website")
    p.set_defaults(fn=cmd_eval)

    p = sub.add_parser("admin", help="Operator commands")
    p.add_argument("action", choices=["set-plan"])
    p.add_argument("--org", required=True)
    p.add_argument("--plan", required=True)
    p.set_defaults(fn=cmd_admin)

    args = parser.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
