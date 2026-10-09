"""Organization-wide dashboard: what needs attention now."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from veridion.api import serializers as S
from veridion.api.deps import Principal, get_principal
from veridion.assessment.diff import diff_runs
from veridion.benchmarking import benchmark
from veridion.db import get_db
from veridion.models import (
    Action,
    AssessmentRun,
    Company,
    CompanyPeer,
    Document,
    Finding,
    Requirement,
    RequirementSet,
    Review,
)

router = APIRouter(tags=["workspace"])


@router.get("/dashboard")
def dashboard(principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> dict:
    org_id = principal.org_id
    companies = {c.id: c for c in db.execute(select(Company).where(Company.org_id == org_id)).scalars()}
    titles = {rs.id: rs.title for rs in db.execute(select(RequirementSet)).scalars()}

    recent_runs = db.execute(select(AssessmentRun).where(AssessmentRun.org_id == org_id)
                             .order_by(AssessmentRun.created_at.desc()).limit(6)).scalars().all()

    latest_runs: list[AssessmentRun] = []
    for cid in companies:
        run = S.latest_run_for(db, org_id, cid)
        if run:
            latest_runs.append(run)

    review_queue, contradictions, changes = [], [], []
    for run in latest_runs:
        findings = db.execute(select(Finding, Requirement).join(Requirement, Requirement.id == Finding.requirement_id)
                              .where(Finding.run_id == run.id)).all()
        # A comment does not resolve a finding; only an accept or override decision does.
        reviewed = set(db.execute(select(func.distinct(Review.finding_id)).where(
            Review.finding_id.in_([f.id for f, _ in findings]),
            Review.decision.in_(["accept", "override"]))).scalars()) if findings else set()
        for f, req in findings:
            item = {"finding_id": f.id, "run_id": run.id, "company_id": run.company_id,
                    "company": companies[run.company_id].name, "display_code": req.display_code,
                    "title": req.title, "status": f.status, "reasons": f.review_reasons[:2],
                    "priority": f.priority.get("P", 0)}
            if f.status == "conflicting":
                contradictions.append({**item, "conflicts": f.conflicts})
            if f.requires_human_review and f.id not in reviewed:
                review_queue.append(item)
        if run.previous_run_id:
            prev = db.get(AssessmentRun, run.previous_run_id)
            if prev is not None:
                d = diff_runs(db, prev, run)
                if d["items"]:
                    changes.append({"company_id": run.company_id, "company": companies[run.company_id].name,
                                    "run_id": run.id, "previous_run_id": prev.id, "summary": d["summary"],
                                    "items": d["items"][:4]})

    ranked = db.execute(select(Action).where(Action.org_id == org_id,
                                             Action.status.in_(["open", "in_progress", "blocked"]))
                        .order_by(Action.priority_score.desc(), Action.created_at)).scalars().all()
    per_company: dict[str, int] = {}
    gaps = []
    for action in ranked:  # at most three per company so one company cannot crowd out the rest
        if per_company.get(action.company_id, 0) < 3:
            gaps.append(action)
            per_company[action.company_id] = per_company.get(action.company_id, 0) + 1
        if len(gaps) == 8:
            break
    recent_docs = db.execute(select(Document).where(Document.org_id == org_id)
                             .order_by(Document.created_at.desc()).limit(6)).scalars().all()

    peer_coverage = []
    focal_ids = [row[0] for row in db.execute(select(func.distinct(CompanyPeer.company_id))
                                              .where(CompanyPeer.org_id == org_id)).all()][:3]
    for cid in focal_ids:
        company = companies.get(cid)
        if company is None:
            continue
        peers = [companies[p] for (p,) in db.execute(select(CompanyPeer.peer_id).where(
            CompanyPeer.company_id == cid)).all() if p in companies]
        latest = S.latest_run_for(db, org_id, cid)
        period = latest.period_label if latest and latest.period_label else "FY2025"
        bench = benchmark(db, org_id, company, peers, period)
        peer_coverage.append({
            "company_id": cid, "company": company.name, "period": period,
            "peers": [p.name for p in peers],
            "metrics": [{"label": r["label"], "coverage": r["coverage"], "comparability": r["comparability"]}
                        for r in bench["rows"]][:6],
        })

    open_actions = int(db.execute(select(func.count()).select_from(Action).where(
        Action.org_id == org_id, Action.status.in_(["open", "in_progress", "blocked"]))).scalar_one())
    return {
        "counts": {"companies": len(companies),
                   "documents": int(db.execute(select(func.count()).select_from(Document).where(
                       Document.org_id == org_id, Document.superseded_at.is_(None))).scalar_one()),
                   "runs": int(db.execute(select(func.count()).select_from(AssessmentRun).where(
                       AssessmentRun.org_id == org_id)).scalar_one()),
                   "open_actions": open_actions},
        "recent_runs": [{**S.run(r, set_title=titles.get(r.requirement_set_id)),
                         "company": companies[r.company_id].name if r.company_id in companies else None}
                        for r in recent_runs],
        "review_queue": sorted(review_queue, key=lambda i: -i["priority"])[:10],
        "contradictions": contradictions[:10],
        "material_gaps": [{**S.action(a), "company": companies[a.company_id].name if a.company_id in companies else None}
                          for a in gaps],
        "changes": changes,
        "recent_documents": [{**S.document(d), "company": companies[d.company_id].name if d.company_id in companies else None}
                             for d in recent_docs],
        "peer_coverage": peer_coverage,
    }

