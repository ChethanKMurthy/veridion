"""Assessment runs: Assessment = f(documents, requirements, rules, model).

A run records every input that determines its result — document versions and
hashes, requirement content hashes, pipeline/rules/prompt versions and model
configuration — so the same inputs can be audited and re-run. Runs are never
overwritten; a re-assessment creates a new run linked to its predecessor.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from veridion import EXTRACTION_VERSION, PIPELINE_VERSION, PROMPT_VERSION, RULES_VERSION
from veridion.assessment.actions import sync_actions
from veridion.assessment.context import AssessmentContext
from veridion.assessment.llm import LLMAssessment, assess_with_model
from veridion.assessment.merge import Merged, merge, rules_only
from veridion.assessment.priority import priority
from veridion.assessment.rules import RulesResult, assess_requirement
from veridion.config import get_settings
from veridion.db import utcnow
from veridion.extraction.periods import Period, parse_period_label
from veridion.jobs import PermanentJobError, enqueue, handler, on_failure
from veridion.llm import get_provider
from veridion.models import (
    ApplicabilityDecision,
    AssessmentRun,
    Company,
    Document,
    Finding,
    FindingEvidence,
    Job,
    Requirement,
    RequirementSet,
)
from veridion.services import audit, entitlements, usage
from veridion.services.documents import current_documents

log = logging.getLogger("veridion.assessment")


class RunError(ValueError):
    pass


def run_period(run: AssessmentRun) -> Period:
    assert run.period_start and run.period_end
    return Period(run.period_label or f"FY{run.period_end.year}", run.period_start, run.period_end, True,
                  run.period_label or "")


def create_run(session: Session, *, org_id: str, company: Company, requirement_set_id: str, mode: str,
               period_label: str, deadline: date | None, user_id: str | None, label: str | None = None,
               enforce_quota: bool = True) -> tuple[AssessmentRun, Job]:
    rs = session.get(RequirementSet, requirement_set_id)
    if rs is None:
        raise RunError("Unknown requirement set.")
    if mode not in ("rules", "hybrid"):
        raise RunError("Mode must be 'rules' or 'hybrid'.")
    if mode == "hybrid" and get_provider() is None:
        raise RunError("AI-assisted assessment is not configured on this deployment. Use rules-only mode.")
    period = parse_period_label(period_label, company.fiscal_year_end)
    if period is None:
        raise RunError(f"Could not understand the period {period_label!r}. Use e.g. FY2025.")
    docs = current_documents(session, org_id, company.id)
    if not docs:
        raise RunError("Upload at least one document before running an assessment.")
    pending = [d.title for d in docs if d.status in ("uploaded", "processing")]
    if pending:
        raise RunError("Some documents are still being processed: " + ", ".join(pending[:3]))
    if not any(d.status == "ready" for d in docs):
        raise RunError("No documents were processed successfully.")
    if enforce_quota:
        entitlements.check_run_quota(session, org_id, hybrid=mode == "hybrid")

    run = AssessmentRun(
        org_id=org_id, company_id=company.id, requirement_set_id=rs.id, mode=mode, status="queued", label=label,
        period_label=period.label, period_start=period.start, period_end=period.end, deadline=deadline,
        created_by=user_id,
    )
    session.add(run)
    session.flush()
    job = enqueue(session, "run_assessment", {"run_id": run.id}, org_id=org_id, max_attempts=2)
    run.job_id = job.id
    usage.record(session, org_id, "assessment_runs", 1, ref_id=run.id)
    if mode == "hybrid":
        usage.record(session, org_id, "hybrid_runs", 1, ref_id=run.id)
    audit.record(session, org_id=org_id, actor_id=user_id, action="assessment.started", entity_type="run",
                 entity_id=run.id, data={"requirement_set": rs.id, "mode": mode, "period": period.label})
    return run, job


@handler("run_assessment")
def run_assessment_job(session: Session, job: Job, progress) -> dict:
    run = session.get(AssessmentRun, job.payload["run_id"])
    if run is None:
        raise PermanentJobError("Run no longer exists.")
    return execute_run(session, run, progress)


@on_failure("run_assessment")
def _run_failed(session: Session, job: Job, exc: Exception) -> None:
    run = session.get(AssessmentRun, job.payload.get("run_id"))
    if run is not None:
        run.status, run.error, run.finished_at = "failed", str(exc)[:1000], utcnow()


def _applicability(session: Session, run: AssessmentRun, set_key: str) -> dict[str, ApplicabilityDecision]:
    decisions = session.execute(
        select(ApplicabilityDecision)
        .where(ApplicabilityDecision.org_id == run.org_id, ApplicabilityDecision.company_id == run.company_id,
               ApplicabilityDecision.set_key == set_key)
        .order_by(ApplicabilityDecision.created_at)
    ).scalars()
    latest: dict[str, ApplicabilityDecision] = {}
    for d in decisions:
        latest[d.requirement_code] = d
    return latest


def execute_run(session: Session, run: AssessmentRun, progress=None) -> dict:
    progress = progress or (lambda *_: None)
    timings: dict[str, float] = {}
    t0 = time.perf_counter()
    run.status, run.started_at, run.error = "running", utcnow(), None
    session.commit()  # make "running" visible and hold no locks during computation

    company = session.get(Company, run.company_id)
    rs = session.get(RequirementSet, run.requirement_set_id)
    assert company is not None and rs is not None
    period = run_period(run)
    docs = [d for d in current_documents(session, run.org_id, company.id) if d.status == "ready"]
    if not docs:
        raise PermanentJobError("No processed documents are available for this company.")

    decisions = _applicability(session, run, rs.key)
    requirements: list[Requirement] = []
    excluded = []
    for req in rs.requirements:
        decision = decisions.get(req.code)
        if decision is not None and not decision.applicable:
            excluded.append({"code": req.code, "display_code": req.display_code, "rationale": decision.rationale,
                             "decided_by": decision.decided_by, "decided_at": decision.created_at.isoformat()})
            continue
        requirements.append(req)

    with session.no_autoflush:
        previous = session.execute(
            select(AssessmentRun)
            .join(RequirementSet, RequirementSet.id == AssessmentRun.requirement_set_id)
            .where(AssessmentRun.org_id == run.org_id, AssessmentRun.company_id == run.company_id,
                   AssessmentRun.status == "completed", AssessmentRun.id != run.id, RequirementSet.key == rs.key)
            .order_by(AssessmentRun.created_at.desc()).limit(1)
        ).scalar_one_or_none()
    manifest = {
        "documents": [{"id": d.id, "title": d.title, "version": d.version, "lineage_id": d.lineage_id,
                       "sha256": d.sha256, "pipeline_version": d.pipeline_version,
                       "extraction_version": d.extraction_version, "period": d.period_label} for d in docs],
        "requirement_set": {"id": rs.id, "content_hash": rs.content_hash},
        "requirements": {r.code: r.content_hash for r in requirements},
        "period": {"label": period.label, "start": period.start.isoformat(), "end": period.end.isoformat()},
    }

    progress("loading", 5, f"Loading evidence from {len(docs)} documents")
    with session.no_autoflush:
        ctx = AssessmentContext.load(session, run.org_id, company.id, docs, period)
    timings["load_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    t1 = time.perf_counter()
    rules_results: dict[str, RulesResult] = {}
    for i, req in enumerate(requirements):
        rules_results[req.id] = assess_requirement(req, ctx)
        progress("rules", 10 + 30 * (i + 1) / max(1, len(requirements)), f"Checked {req.display_code}")
    timings["rules_ms"] = round((time.perf_counter() - t1) * 1000, 1)

    model_results: dict[str, LLMAssessment | Exception] = {}
    llm_stats = {"calls": 0, "cached": 0, "prompt_tokens": 0, "completion_tokens": 0, "failures": 0}
    llm_meta: dict = {}
    if run.mode == "hybrid":
        provider = get_provider()
        if provider is None:
            raise PermanentJobError("AI-assisted mode was requested but no model provider is configured.")
        llm_meta = {"llm_provider": provider.name, "llm_model": provider.model,
                    "llm_config": {"temperature": 0, "max_tokens": 1400, "structured_output": "json_schema",
                                   "reasoning_effort": "low" if "gpt-oss" in provider.model else None}}
        t2 = time.perf_counter()
        done = 0

        def call(req: Requirement):
            try:
                return req.id, assess_with_model(provider, req, rules_results[req.id], ctx)
            except Exception as exc:
                log.warning("Model assessment failed for %s: %s", req.display_code, exc)
                return req.id, exc

        with ThreadPoolExecutor(max_workers=max(1, get_settings().llm_max_concurrency)) as pool:
            for req_id, result in pool.map(call, requirements):
                model_results[req_id] = result
                done += 1
                progress("model", 40 + 45 * done / max(1, len(requirements)),
                         f"Model assessed {done} of {len(requirements)} requirements")
        timings["model_ms"] = round((time.perf_counter() - t2) * 1000, 1)

    # --- persist (single write transaction) -------------------------------------
    t3 = time.perf_counter()
    session.query(Finding).filter(Finding.run_id == run.id).delete()  # idempotent retries
    run.previous_run_id = previous.id if previous else None
    run.input_manifest = manifest
    run.excluded_requirements = excluded
    run.pipeline_version, run.extraction_version = PIPELINE_VERSION, EXTRACTION_VERSION
    run.rules_version, run.prompt_version = RULES_VERSION, (PROMPT_VERSION if run.mode == "hybrid" else None)
    for attr, value in llm_meta.items():
        setattr(run, attr, value)
    pairs: list[tuple[Finding, Requirement]] = []
    counts: dict[str, int] = {}
    for req in requirements:
        rules = rules_results[req.id]
        model = model_results.get(req.id)
        llm_output = None
        if isinstance(model, LLMAssessment):
            merged: Merged = merge(req, rules, model)
            method = "hybrid"
            response = model.response
            llm_stats["calls"] += 1
            if response is not None:
                llm_stats["cached"] += int(response.cached)
                llm_stats["prompt_tokens"] += int(response.usage.get("prompt_tokens") or 0)
                llm_stats["completion_tokens"] += int(response.usage.get("completion_tokens") or 0)
            llm_output = {"status": model.status, "rationale": model.rationale, "confidence": model.confidence,
                          "requires_human_review": model.requires_human_review,
                          "judgements": {k: {"verdict": j.verdict, "note": j.note, "evidence_ids": j.evidence_ids}
                                         for k, j in model.judgements.items()},
                          "missing_elements": model.missing_elements, "overrides": merged.model_overrides,
                          "cached": bool(response and response.cached), "usage": response.usage if response else {}}
            citation_check = model.citation_check()
        else:
            merged = rules_only(rules)
            method = "rules"
            citation_check = {"cited": sorted({p for e in rules.elements for p in e.passage_ids}), "invalid": [],
                              "valid_ratio": 1.0}
            if isinstance(model, Exception):
                llm_stats["failures"] += 1
                merged.review_reasons.append(f"Model assessment unavailable ({type(model).__name__}); "
                                             "rules-only result shown.")
                merged.requires_human_review = True

        finding = Finding(
            org_id=run.org_id, run_id=run.id, company_id=company.id, requirement_id=req.id,
            requirement_code=req.code, status=merged.status, completeness=merged.completeness,
            confidence=merged.confidence, rationale=merged.rationale, rules_rationale=rules.rationale,
            element_results=[e.to_dict() for e in merged.elements],
            missing_elements=[e.label for e in merged.elements if e.status == "missing"],
            requires_human_review=merged.requires_human_review, review_reasons=merged.review_reasons,
            method=method, rules_status=rules.status, llm_status=model.status if isinstance(model, LLMAssessment) else None,
            llm_output=llm_output, citation_check=citation_check,
            conflicts=[c.to_dict(ctx) for c in rules.conflicts],
            priority=priority(req.importance, merged.status, merged.completeness, run.deadline),
            retrieval=rules.retrieval,
        )
        session.add(finding)
        session.flush()
        _link_evidence(session, finding, merged, rules)
        pairs.append((finding, req))
        counts[merged.status] = counts.get(merged.status, 0) + 1

    action_stats = sync_actions(session, run, rs.key, pairs)
    timings["persist_ms"] = round((time.perf_counter() - t3) * 1000, 1)
    timings["total_ms"] = round((time.perf_counter() - t0) * 1000, 1)

    run.summary = {
        "counts": counts, "requirements": len(requirements), "excluded": len(excluded),
        "average_completeness": round(sum(f.completeness for f, _ in pairs) / max(1, len(pairs)), 3),
        "needs_review": sum(1 for f, _ in pairs if f.requires_human_review),
        "actions": action_stats,
    }
    run.metrics = {"timings": timings, "llm": llm_stats, "documents": len(docs), "passages": len(ctx.passages),
                   "extracted_metrics": len(ctx.metrics)}
    run.status, run.finished_at = "completed", utcnow()
    tokens = llm_stats["prompt_tokens"] + llm_stats["completion_tokens"]
    if tokens:
        usage.record(session, run.org_id, "llm_tokens", tokens, ref_id=run.id)
    audit.record(session, org_id=run.org_id, actor_id=run.created_by, action="assessment.completed",
                 entity_type="run", entity_id=run.id, data={"counts": counts})
    progress("done", 100, "Assessment complete")
    return {"run_id": run.id, "counts": counts}


def _link_evidence(session: Session, finding: Finding, merged: Merged, rules: RulesResult) -> None:
    rank = 0
    linked: dict[str, FindingEvidence] = {}
    for element in merged.elements:
        if element.status != "satisfied":
            continue
        for pid in element.passage_ids:
            if pid in linked:
                if element.key not in linked[pid].element_keys:
                    linked[pid].element_keys = [*linked[pid].element_keys, element.key]
                continue
            fe = FindingEvidence(finding_id=finding.id, passage_id=pid, role="supporting",
                                 element_keys=[element.key], rank=rank, score=element.weight,
                                 note=element.note[:500])
            session.add(fe)
            linked[pid] = fe
            rank += 1
    for conflict in rules.conflicts:
        for value in (conflict.low, conflict.high):
            if value.passage_id in linked:
                linked[value.passage_id].role = "conflicting"
                continue
            fe = FindingEvidence(finding_id=finding.id, passage_id=value.passage_id, role="conflicting",
                                 element_keys=[], metric_id=value.id, rank=rank, score=1.0,
                                 note=f"{value.value:,.4g} {value.unit} for {conflict.period_label}")
            session.add(fe)
            linked[value.passage_id] = fe
            rank += 1
    hit_scores = {h["passage_id"]: h["score"] for h in rules.retrieval.get("hits", [])}
    for pid in merged.related_passage_ids:
        if pid in linked:
            continue
        fe = FindingEvidence(finding_id=finding.id, passage_id=pid, role="related", element_keys=[], rank=rank,
                             score=float(hit_scores.get(pid, 0.0)), note="Related passage for review")
        session.add(fe)
        linked[pid] = fe
        rank += 1
    session.flush()


def stale_findings(session: Session, run: AssessmentRun) -> list[dict]:
    """Findings whose cited documents have since been replaced by a newer version."""
    doc_ids = [d["id"] for d in run.input_manifest.get("documents", [])]
    if not doc_ids:
        return []
    superseded = {d.id: d for d in session.execute(
        select(Document).where(Document.id.in_(doc_ids), Document.superseded_at.is_not(None))
    ).scalars()}
    if not superseded:
        return []
    from veridion.models import Passage

    rows = session.execute(
        select(Finding.id, Finding.requirement_code, Passage.document_id)
        .join(FindingEvidence, FindingEvidence.finding_id == Finding.id)
        .join(Passage, Passage.id == FindingEvidence.passage_id)
        .where(Finding.run_id == run.id, Passage.document_id.in_(list(superseded)))
    ).all()
    out: dict[str, dict] = {}
    for finding_id, code, doc_id in rows:
        entry = out.setdefault(finding_id, {"finding_id": finding_id, "requirement_code": code, "documents": []})
        doc = superseded[doc_id]
        if doc.id not in [d["id"] for d in entry["documents"]]:
            entry["documents"].append({"id": doc.id, "title": doc.title, "version": doc.version,
                                       "superseded_by": doc.superseded_by})
    return list(out.values())
