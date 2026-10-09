"""Requirement catalogues, assessment runs, findings, reviews, diffs, reports and actions."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from veridion.api import serializers as S
from veridion.api.deps import REVIEW_ROLES, WRITE_ROLES, Principal, get_principal, require_roles
from veridion.assessment.diff import diff_runs
from veridion.assessment.engine import create_run, stale_findings
from veridion.db import get_db
from veridion.models import Action, AssessmentRun, Job, Requirement, RequirementSet, Review
from veridion.models.assessment import ACTION_STATUSES, STATUSES
from veridion.reports import (
    evidence_package,
    finding_trail,
    findings_csv,
    findings_markdown,
    report_data,
    run_findings,
)
from veridion.services import audit, entitlements

router = APIRouter(tags=["assessments"])


# --- requirement catalogues -------------------------------------------------------

@router.get("/requirement-sets")
def requirement_sets(principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> list[dict]:
    counts = dict(db.execute(select(Requirement.set_id, func.count()).group_by(Requirement.set_id)).all())
    sets = db.execute(select(RequirementSet).order_by(RequirementSet.key, RequirementSet.version)).scalars().all()
    return [S.requirement_set(rs, count=counts.get(rs.id, 0)) for rs in sets]


@router.get("/requirement-sets/{set_id}")
def requirement_set(set_id: str, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> dict:
    rs = db.get(RequirementSet, set_id)
    if rs is None:
        raise HTTPException(404, "Requirement set not found")
    return S.requirement_set(rs, with_requirements=True)


# --- runs ----------------------------------------------------------------------------

class RunIn(BaseModel):
    requirement_set_id: str
    mode: str = Field(default="rules", pattern="^(rules|hybrid)$")
    period_label: str = Field(default="FY2025", max_length=20)
    deadline: date | None = None
    label: str | None = Field(default=None, max_length=200)


def _set_titles(db: Session) -> dict[str, str]:
    return {rs.id: rs.title for rs in db.execute(select(RequirementSet)).scalars()}


@router.post("/companies/{company_id}/runs", status_code=201)
def start_run(company_id: str, body: RunIn, principal: Principal = Depends(require_roles(*WRITE_ROLES)),
              db: Session = Depends(get_db)) -> dict:
    company = S.company_or_404(db, principal.org_id, company_id)
    run, job = create_run(db, org_id=principal.org_id, company=company, requirement_set_id=body.requirement_set_id,
                          mode=body.mode, period_label=body.period_label, deadline=body.deadline,
                          user_id=principal.user_id, label=body.label)
    return S.run(run, job_row=job, set_title=_set_titles(db).get(run.requirement_set_id))


@router.get("/companies/{company_id}/runs")
def list_runs(company_id: str, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> list[dict]:
    company = S.company_or_404(db, principal.org_id, company_id)
    runs = db.execute(select(AssessmentRun).where(AssessmentRun.org_id == principal.org_id,
                                                  AssessmentRun.company_id == company.id)
                      .order_by(AssessmentRun.created_at.desc())).scalars().all()
    titles = _set_titles(db)
    jobs = {j.id: j for j in db.execute(select(Job).where(Job.id.in_([r.job_id for r in runs if r.job_id]))).scalars()}
    return [S.run(r, job_row=jobs.get(r.job_id or ""), set_title=titles.get(r.requirement_set_id)) for r in runs]


@router.get("/runs/{run_id}")
def get_run(run_id: str, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> dict:
    run = S.run_or_404(db, principal.org_id, run_id)
    job = db.get(Job, run.job_id) if run.job_id else None
    out = S.run(run, job_row=job, set_title=_set_titles(db).get(run.requirement_set_id))
    out["stale_findings"] = stale_findings(db, run) if run.status == "completed" else []
    out["created_by_name"] = S.user_name(db, run.created_by)
    return out


@router.get("/runs/{run_id}/findings")
def list_findings(run_id: str, status: str | None = None, review: str | None = None,
                  principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> list[dict]:
    run = S.run_or_404(db, principal.org_id, run_id)
    rows = run_findings(db, run)
    if status:
        rows = [r for r in rows if r["status"] == status]
    if review == "needed":
        rows = [r for r in rows if r["requires_human_review"] and r["review"]["state"] == "unreviewed"]
    elif review:
        rows = [r for r in rows if r["review"]["state"] == review]
    return rows


@router.get("/runs/{run_id}/diff")
def run_diff(run_id: str, against: str | None = None, principal: Principal = Depends(get_principal),
             db: Session = Depends(get_db)) -> dict:
    after = S.run_or_404(db, principal.org_id, run_id)
    before_id = against or after.previous_run_id
    if not before_id:
        raise HTTPException(404, "There is no earlier run to compare with.")
    before = S.run_or_404(db, principal.org_id, before_id)
    if before.company_id != after.company_id:
        raise HTTPException(400, "Runs belong to different companies.")
    if before.created_at > after.created_at:
        before, after = after, before
    return diff_runs(db, before, after)


@router.get("/runs/{run_id}/report")
def run_report(run_id: str, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> dict:
    run = S.run_or_404(db, principal.org_id, run_id)
    if run.status != "completed":
        raise HTTPException(409, "The run has not completed yet.")
    return report_data(db, run)


@router.get("/runs/{run_id}/export")
def export_run(run_id: str, format: str = Query(default="json", pattern="^(json|csv|md)$"),
               principal: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    run = S.run_or_404(db, principal.org_id, run_id)
    if run.status != "completed":
        raise HTTPException(409, "The run has not completed yet.")
    plan = entitlements.plan_for(db, principal.org_id)
    if format not in plan.exports:
        raise HTTPException(402, f"{format.upper()} export is not included in your plan.")
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action="run.exported", entity_type="run",
                 entity_id=run.id, data={"format": format})
    filename = f"veridion-{run.id}.{format}"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    if format == "json":
        return JSONResponse(evidence_package(db, run), headers=headers)
    if format == "csv":
        return PlainTextResponse(findings_csv(db, run), media_type="text/csv", headers=headers)
    return PlainTextResponse(findings_markdown(db, run), media_type="text/markdown", headers=headers)


# --- findings and reviews ------------------------------------------------------------------

class ReviewIn(BaseModel):
    decision: str = Field(pattern="^(accept|override|comment)$")
    new_status: str | None = None
    note: str = Field(default="", max_length=4000)


@router.get("/findings/{finding_id}")
def get_finding(finding_id: str, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> dict:
    finding = S.finding_or_404(db, principal.org_id, finding_id)
    return finding_trail(db, finding)


@router.post("/findings/{finding_id}/reviews", status_code=201)
def review_finding(finding_id: str, body: ReviewIn, principal: Principal = Depends(require_roles(*REVIEW_ROLES)),
                   db: Session = Depends(get_db)) -> dict:
    finding = S.finding_or_404(db, principal.org_id, finding_id)
    if body.decision == "override":
        if body.new_status not in STATUSES:
            raise HTTPException(422, "An override needs a new status.")
        if not body.note.strip():
            raise HTTPException(422, "Explain the override so the decision can be audited.")
    if body.decision == "comment" and not body.note.strip():
        raise HTTPException(422, "A comment needs text.")
    rv = Review(org_id=principal.org_id, finding_id=finding.id, reviewer_id=principal.user_id,
                reviewer_name=principal.user.name, decision=body.decision, previous_status=finding.status,
                new_status=body.new_status if body.decision == "override" else None, note=body.note.strip())
    db.add(rv)
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action=f"finding.{body.decision}",
                 entity_type="finding", entity_id=finding.id,
                 data={"new_status": rv.new_status, "previous_status": finding.status})
    db.flush()
    return S.review(rv)


# --- actions ---------------------------------------------------------------------------------

class ActionPatch(BaseModel):
    status: str | None = None
    owner: str | None = Field(default=None, max_length=200)
    due_date: date | None = None


@router.get("/companies/{company_id}/actions")
def list_actions(company_id: str, status: str | None = None, principal: Principal = Depends(get_principal),
                 db: Session = Depends(get_db)) -> list[dict]:
    company = S.company_or_404(db, principal.org_id, company_id)
    q = select(Action).where(Action.org_id == principal.org_id, Action.company_id == company.id)
    if status == "open":
        q = q.where(Action.status.in_(["open", "in_progress", "blocked"]))
    elif status:
        q = q.where(Action.status == status)
    rows = db.execute(q.order_by(Action.priority_score.desc(), Action.created_at)).scalars().all()
    return [S.action(a) for a in rows]


@router.patch("/actions/{action_id}")
def patch_action(action_id: str, body: ActionPatch, principal: Principal = Depends(require_roles(*REVIEW_ROLES)),
                 db: Session = Depends(get_db)) -> dict:
    action = S.action_or_404(db, principal.org_id, action_id)
    changes = body.model_dump(exclude_unset=True)
    if "status" in changes and changes["status"] not in ACTION_STATUSES:
        raise HTTPException(422, f"status must be one of {', '.join(ACTION_STATUSES)}")
    for key, value in changes.items():
        setattr(action, key, value)
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action="action.updated",
                 entity_type="action", entity_id=action.id, data={k: str(v) for k, v in changes.items()})
    db.flush()
    return S.action(action)


@router.get("/jobs/{job_id}")
def get_job(job_id: str, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> dict:
    job = db.get(Job, job_id)
    if job is None or job.org_id != principal.org_id:
        raise HTTPException(404, "Job not found")
    return S.job(job) or {}
