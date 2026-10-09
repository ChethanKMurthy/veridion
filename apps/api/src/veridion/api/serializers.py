"""Tenant-scoped lookups and JSON serialisers shared by the routes."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from veridion.api.errors import NotFound
from veridion.assessment.context import short_doc_name
from veridion.catalog import set_status
from veridion.jobs import LIVE_PROGRESS
from veridion.models import (
    Action,
    AssessmentRun,
    Company,
    Document,
    Finding,
    Job,
    Passage,
    Requirement,
    RequirementSet,
    Review,
    User,
)


def iso(value: date | datetime | None) -> str | None:
    return value.isoformat() if value else None


# --- tenant-scoped getters (404 for anything outside the caller's organization) ---

def company_or_404(db: Session, org_id: str, company_id: str) -> Company:
    company = db.get(Company, company_id)
    if company is None or company.org_id != org_id:
        raise NotFound("Company")
    return company


def document_or_404(db: Session, org_id: str, document_id: str) -> Document:
    doc = db.get(Document, document_id)
    if doc is None or doc.org_id != org_id:
        raise NotFound("Document")
    return doc


def run_or_404(db: Session, org_id: str, run_id: str) -> AssessmentRun:
    run = db.get(AssessmentRun, run_id)
    if run is None or run.org_id != org_id:
        raise NotFound("Assessment run")
    return run


def finding_or_404(db: Session, org_id: str, finding_id: str) -> Finding:
    finding = db.get(Finding, finding_id)
    if finding is None or finding.org_id != org_id:
        raise NotFound("Finding")
    return finding


def passage_or_404(db: Session, org_id: str, passage_id: str) -> Passage:
    passage = db.get(Passage, passage_id)
    if passage is None or passage.org_id != org_id:
        raise NotFound("Passage")
    return passage


def action_or_404(db: Session, org_id: str, action_id: str) -> Action:
    action = db.get(Action, action_id)
    if action is None or action.org_id != org_id:
        raise NotFound("Action")
    return action


# --- serialisers ------------------------------------------------------------

def company(c: Company, *, extra: dict | None = None) -> dict:
    return {
        "id": c.id, "name": c.name, "industry": c.industry, "country": c.country, "size_band": c.size_band,
        "fiscal_year_end": c.fiscal_year_end, "website": c.website, "description": c.description,
        "is_sample": c.is_sample, "created_at": iso(c.created_at), **(extra or {}),
    }


def job(j: Job | None) -> dict | None:
    if j is None:
        return None
    progress = LIVE_PROGRESS.get(j.id) or j.progress
    return {"id": j.id, "kind": j.kind, "status": j.status, "progress": progress, "attempts": j.attempts,
            "error": (j.error or "").split("\n")[0][:500] or None, "created_at": iso(j.created_at),
            "finished_at": iso(j.finished_at)}


def document(d: Document, *, job_row: Job | None = None) -> dict:
    return {
        "id": d.id, "company_id": d.company_id, "lineage_id": d.lineage_id, "version": d.version, "title": d.title,
        "short_name": short_doc_name(d), "doc_type": d.doc_type, "filename": d.filename, "sha256": d.sha256,
        "size_bytes": d.size_bytes, "page_count": d.page_count, "page_sizes": d.page_sizes,
        "period_label": d.period_label, "period_start": iso(d.period_start), "period_end": iso(d.period_end),
        "published_on": iso(d.published_on), "source_url": d.source_url, "status": d.status, "error": d.error,
        "ocr_pages": d.ocr_pages, "stats": d.processing_stats, "pipeline_version": d.pipeline_version,
        "extraction_version": d.extraction_version, "is_sample": d.is_sample, "created_at": iso(d.created_at),
        "processed_at": iso(d.processed_at), "superseded_at": iso(d.superseded_at), "superseded_by": d.superseded_by,
        "job": job(job_row),
    }


def passage(p: Passage, doc: Document | None = None) -> dict:
    return {
        "id": p.id, "document_id": p.document_id, "page": p.page, "ordinal": p.ordinal, "kind": p.kind,
        "section": p.section, "text": p.text, "bbox": p.bbox, "extraction_method": p.extraction_method,
        "confidence": p.confidence, "table_ref": p.table_ref, "cells": p.cells,
        "document": ({"id": doc.id, "title": doc.title, "short_name": short_doc_name(doc), "version": doc.version,
                      "doc_type": doc.doc_type, "period_label": doc.period_label, "page_sizes": doc.page_sizes,
                      "superseded_at": iso(doc.superseded_at)} if doc else None),
    }


def requirement_set(rs: RequirementSet, *, with_requirements: bool = False, count: int | None = None) -> dict:
    out = {
        "id": rs.id, "key": rs.key, "version": rs.version, "title": rs.title, "framework": rs.framework,
        "description": rs.description, "standards": rs.standards, "effective_from": iso(rs.effective_from),
        "effective_to": iso(rs.effective_to), "effective_rule": rs.effective_rule, "status": set_status(rs),
        "review_status": rs.review_status, "changelog": rs.changelog, "supersedes": rs.supersedes,
        "succeeded_by": rs.succeeded_by, "notes": rs.notes, "content_hash": rs.content_hash,
        "requirement_count": count if count is not None else len(rs.requirements),
    }
    if with_requirements:
        out["requirements"] = [requirement(r) for r in rs.requirements]
    return out


def requirement(r: Requirement) -> dict:
    return {
        "id": r.id, "set_id": r.set_id, "code": r.code, "display_code": r.display_code, "title": r.title,
        "topic": r.topic, "summary": r.summary, "applicability": r.applicability, "importance": r.importance,
        "elements": r.elements, "metric_keys": r.metric_keys, "search_terms": r.search_terms,
        "source_reference": r.source_reference, "source_url": r.source_url, "content_hash": r.content_hash,
    }


def run(r: AssessmentRun, *, job_row: Job | None = None, set_title: str | None = None) -> dict:
    return {
        "id": r.id, "company_id": r.company_id, "requirement_set_id": r.requirement_set_id,
        "requirement_set_title": set_title, "mode": r.mode, "status": r.status, "label": r.label,
        "period_label": r.period_label, "period_start": iso(r.period_start), "period_end": iso(r.period_end),
        "deadline": iso(r.deadline), "pipeline_version": r.pipeline_version,
        "extraction_version": r.extraction_version, "rules_version": r.rules_version,
        "prompt_version": r.prompt_version, "llm_provider": r.llm_provider, "llm_model": r.llm_model,
        "llm_config": r.llm_config, "input_manifest": r.input_manifest, "excluded_requirements": r.excluded_requirements,
        "metrics": r.metrics, "summary": r.summary, "previous_run_id": r.previous_run_id, "error": r.error,
        "created_by": r.created_by, "created_at": iso(r.created_at), "started_at": iso(r.started_at),
        "finished_at": iso(r.finished_at), "job": job(job_row),
    }


def review_state(reviews: list[Review], finding: Finding) -> dict:
    state, effective, latest = "unreviewed", finding.status, None
    for rv in reviews:
        if rv.decision == "accept":
            state, effective, latest = "accepted", finding.status, rv
        elif rv.decision == "override":
            state, effective, latest = "overridden", rv.new_status or finding.status, rv
    return {"state": state, "effective_status": effective,
            "latest": review(latest) if latest else None, "count": len(reviews)}


def review(rv: Review) -> dict:
    return {"id": rv.id, "finding_id": rv.finding_id, "reviewer_id": rv.reviewer_id,
            "reviewer_name": rv.reviewer_name, "decision": rv.decision, "previous_status": rv.previous_status,
            "new_status": rv.new_status, "note": rv.note, "created_at": iso(rv.created_at)}


def finding_summary(f: Finding, req: Requirement, *, reviews: list[Review], evidence_count: int,
                    primary: dict | None = None) -> dict:
    return {
        "id": f.id, "run_id": f.run_id, "requirement_id": f.requirement_id, "requirement_code": f.requirement_code,
        "display_code": req.display_code, "title": req.title, "topic": req.topic, "importance": req.importance,
        "status": f.status, "completeness": f.completeness, "confidence": f.confidence,
        "requires_human_review": f.requires_human_review, "review_reasons": f.review_reasons,
        "missing_elements": f.missing_elements, "method": f.method, "rules_status": f.rules_status,
        "llm_status": f.llm_status, "priority": f.priority, "rationale": f.rationale,
        "evidence_count": evidence_count, "primary_evidence": primary, "conflicts": f.conflicts,
        "review": review_state(reviews, f), "created_at": iso(f.created_at),
    }


def action(a: Action) -> dict:
    return {
        "id": a.id, "company_id": a.company_id, "finding_id": a.finding_id, "run_id": a.run_id, "set_key": a.set_key,
        "requirement_code": a.requirement_code, "gap_key": a.gap_key, "title": a.title, "detail": a.detail,
        "rationale": a.rationale, "owner": a.owner, "due_date": iso(a.due_date), "effort": a.effort,
        "priority_score": a.priority_score, "priority_components": a.priority_components, "status": a.status,
        "depends_on": a.depends_on, "gap_closed_run_id": a.gap_closed_run_id, "created_at": iso(a.created_at),
        "updated_at": iso(a.updated_at),
    }


def user_name(db: Session, user_id: str | None) -> str | None:
    if not user_id:
        return None
    u = db.get(User, user_id)
    return u.name if u else None


def latest_run_for(db: Session, org_id: str, company_id: str) -> AssessmentRun | None:
    return db.execute(
        select(AssessmentRun).where(AssessmentRun.org_id == org_id, AssessmentRun.company_id == company_id,
                                    AssessmentRun.status == "completed")
        .order_by(AssessmentRun.created_at.desc()).limit(1)
    ).scalar_one_or_none()


def count(db: Session, stmt) -> int:
    return int(db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one())
