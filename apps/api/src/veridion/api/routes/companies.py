"""Companies, peers, applicability decisions, metrics and benchmarking."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from veridion.api import serializers as S
from veridion.api.deps import ADMIN_ROLES, WRITE_ROLES, Principal, get_principal, require_roles
from veridion.benchmarking import benchmark, company_metrics
from veridion.db import get_db
from veridion.models import (
    ApplicabilityDecision,
    AssessmentRun,
    Company,
    CompanyPeer,
    Document,
    Finding,
    FindingEvidence,
    RequirementSet,
)
from veridion.services import audit, entitlements
from veridion.services.documents import current_documents

router = APIRouter(tags=["companies"])

_FYE = re.compile(r"^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")


class CompanyIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    industry: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=80)
    size_band: str | None = Field(default=None, max_length=40)
    fiscal_year_end: str = "12-31"
    website: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("fiscal_year_end")
    @classmethod
    def _fye(cls, v: str) -> str:
        if not _FYE.match(v):
            raise ValueError("Use MM-DD, e.g. 12-31 or 03-31")
        return v


class CompanyPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    industry: str | None = None
    country: str | None = None
    size_band: str | None = None
    fiscal_year_end: str | None = None
    website: str | None = None
    description: str | None = None


class PeersIn(BaseModel):
    peer_ids: list[str] = Field(max_length=10)


class ApplicabilityIn(BaseModel):
    set_key: str
    requirement_code: str
    applicable: bool
    rationale: str = Field(min_length=5, max_length=2000)


def _peers(db: Session, org_id: str, company_id: str) -> list[Company]:
    rows = db.execute(select(Company).join(CompanyPeer, CompanyPeer.peer_id == Company.id)
                      .where(CompanyPeer.company_id == company_id, CompanyPeer.org_id == org_id)
                      .order_by(Company.name)).scalars().all()
    return list(rows)


def _company_card(db: Session, org_id: str, c: Company) -> dict:
    docs = current_documents(db, org_id, c.id)
    latest = S.latest_run_for(db, org_id, c.id)
    return S.company(c, extra={
        "document_count": len(docs),
        "documents_ready": sum(1 for d in docs if d.status == "ready"),
        "pages": sum(d.page_count or 0 for d in docs),
        "periods": sorted({d.period_label for d in docs if d.period_label}),
        "latest_run": {"id": latest.id, "summary": latest.summary, "finished_at": S.iso(latest.finished_at),
                       "requirement_set_id": latest.requirement_set_id, "mode": latest.mode,
                       "period_label": latest.period_label} if latest else None,
        "peer_ids": [p.id for p in _peers(db, org_id, c.id)],
    })


@router.get("/companies")
def list_companies(principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(Company).where(Company.org_id == principal.org_id).order_by(Company.name)).scalars()
    return [_company_card(db, principal.org_id, c) for c in rows]


@router.post("/companies", status_code=201)
def create_company(body: CompanyIn, principal: Principal = Depends(require_roles(*WRITE_ROLES)),
                   db: Session = Depends(get_db)) -> dict:
    entitlements.check_company_quota(db, principal.org_id)
    c = Company(org_id=principal.org_id, created_by=principal.user_id, **body.model_dump())
    db.add(c)
    db.flush()
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action="company.created",
                 entity_type="company", entity_id=c.id, data={"name": c.name})
    return _company_card(db, principal.org_id, c)


@router.get("/companies/{company_id}")
def get_company(company_id: str, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> dict:
    c = S.company_or_404(db, principal.org_id, company_id)
    card = _company_card(db, principal.org_id, c)
    card["peers"] = [S.company(p) for p in _peers(db, principal.org_id, c.id)]
    return card


@router.patch("/companies/{company_id}")
def patch_company(company_id: str, body: CompanyPatch, principal: Principal = Depends(require_roles(*WRITE_ROLES)),
                  db: Session = Depends(get_db)) -> dict:
    c = S.company_or_404(db, principal.org_id, company_id)
    changes = body.model_dump(exclude_unset=True)
    if "fiscal_year_end" in changes and changes["fiscal_year_end"] and not _FYE.match(changes["fiscal_year_end"]):
        raise HTTPException(422, "fiscal_year_end must be MM-DD")
    for key, value in changes.items():
        setattr(c, key, value)
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action="company.updated",
                 entity_type="company", entity_id=c.id, data=changes)
    return _company_card(db, principal.org_id, c)


@router.delete("/companies/{company_id}")
def delete_company(company_id: str, principal: Principal = Depends(require_roles(*ADMIN_ROLES)),
                   db: Session = Depends(get_db)) -> dict:
    c = S.company_or_404(db, principal.org_id, company_id)
    if db.execute(select(AssessmentRun.id).where(AssessmentRun.company_id == c.id).limit(1)).first():
        raise HTTPException(409, "This company has assessment history. Archive it instead of deleting it.")
    db.execute(CompanyPeer.__table__.delete().where(
        (CompanyPeer.company_id == c.id) | (CompanyPeer.peer_id == c.id)))
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action="company.deleted",
                 entity_type="company", entity_id=c.id, data={"name": c.name})
    db.delete(c)
    return {"ok": True}


@router.put("/companies/{company_id}/peers")
def set_peers(company_id: str, body: PeersIn, principal: Principal = Depends(require_roles(*WRITE_ROLES)),
              db: Session = Depends(get_db)) -> dict:
    c = S.company_or_404(db, principal.org_id, company_id)
    peer_ids = list(dict.fromkeys(p for p in body.peer_ids if p != c.id))
    for pid in peer_ids:
        S.company_or_404(db, principal.org_id, pid)
    db.execute(CompanyPeer.__table__.delete().where(CompanyPeer.company_id == c.id))
    for pid in peer_ids:
        db.add(CompanyPeer(company_id=c.id, peer_id=pid, org_id=principal.org_id))
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action="company.peers_set",
                 entity_type="company", entity_id=c.id, data={"peer_ids": peer_ids})
    db.flush()
    return {"peer_ids": peer_ids}


@router.get("/companies/{company_id}/metrics")
def metrics(company_id: str, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> list[dict]:
    c = S.company_or_404(db, principal.org_id, company_id)
    return company_metrics(db, principal.org_id, c)


@router.get("/companies/{company_id}/benchmark")
def company_benchmark(company_id: str, period: str = "FY2025", principal: Principal = Depends(get_principal),
                      db: Session = Depends(get_db)) -> dict:
    c = S.company_or_404(db, principal.org_id, company_id)
    if not re.fullmatch(r"(?:FY|CY)?\d{4}", period):
        raise HTTPException(422, "period must look like FY2025")
    return benchmark(db, principal.org_id, c, _peers(db, principal.org_id, c.id), period)


@router.get("/companies/{company_id}/overview")
def overview(company_id: str, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> dict:
    """Everything the company intelligence view needs in one request."""
    org_id = principal.org_id
    c = S.company_or_404(db, org_id, company_id)
    docs = current_documents(db, org_id, c.id)
    all_metrics = company_metrics(db, org_id, c)
    runs = db.execute(select(AssessmentRun).where(AssessmentRun.org_id == org_id, AssessmentRun.company_id == c.id)
                      .order_by(AssessmentRun.created_at.desc()).limit(10)).scalars().all()
    set_titles = {rs.id: rs.title for rs in db.execute(select(RequirementSet)).scalars()}
    latest = next((r for r in runs if r.status == "completed"), None)

    # Key disclosures: one value per metric for the latest period present, with the prior period for change.
    by_key: dict[str, list[dict]] = {}
    for m in all_metrics:
        if m["qualifiers"].get("base_year"):
            continue
        by_key.setdefault(m["metric_key"], []).append(m)
    key_disclosures = []
    for key, values in by_key.items():
        periods = sorted({v["period_end"] for v in values if v["period_end"]}, reverse=True)
        if not periods:
            continue
        current = max((v for v in values if v["period_end"] == periods[0]), key=lambda v: v["confidence"])
        prior = None
        if len(periods) > 1:
            prior = max((v for v in values if v["period_end"] == periods[1]), key=lambda v: v["confidence"])
        change = None
        if prior and prior["normalized_value"] and current["normalized_value"] is not None and \
                prior["normalized_unit"] == current["normalized_unit"]:
            change = (current["normalized_value"] - prior["normalized_value"]) / abs(prior["normalized_value"])
        key_disclosures.append({"metric_key": key, "label": current["label"], "current": current, "prior": prior,
                                "change": round(change, 4) if change is not None else None,
                                "sources": len(values)})
    key_disclosures.sort(key=lambda k: k["metric_key"])

    unresolved: list[dict] = []
    if latest:
        findings = db.execute(select(Finding).where(Finding.run_id == latest.id)).scalars().all()
        for f in findings:
            if f.status in ("conflicting", "human_review") or f.requires_human_review:
                unresolved.append({"finding_id": f.id, "requirement_code": f.requirement_code, "status": f.status,
                                   "reasons": f.review_reasons[:3]})

    return {
        "company": S.company(c),
        "peers": [S.company(p) for p in _peers(db, org_id, c.id)],
        "coverage": {
            "documents": len(docs), "ready": sum(1 for d in docs if d.status == "ready"),
            "pages": sum(d.page_count or 0 for d in docs),
            "periods": sorted({d.period_label for d in docs if d.period_label}),
            "doc_types": sorted({d.doc_type for d in docs}),
            "ocr_pages": sum(len(d.ocr_pages or []) for d in docs),
            "metrics": len(all_metrics),
        },
        "documents": [S.document(d) for d in docs],
        "key_disclosures": key_disclosures,
        "latest_run": S.run(latest, set_title=set_titles.get(latest.requirement_set_id)) if latest else None,
        "runs": [S.run(r, set_title=set_titles.get(r.requirement_set_id)) for r in runs],
        "unresolved": unresolved,
    }


@router.get("/companies/{company_id}/applicability")
def get_applicability(company_id: str, set_key: str, principal: Principal = Depends(get_principal),
                      db: Session = Depends(get_db)) -> list[dict]:
    c = S.company_or_404(db, principal.org_id, company_id)
    rows = db.execute(select(ApplicabilityDecision).where(
        ApplicabilityDecision.org_id == principal.org_id, ApplicabilityDecision.company_id == c.id,
        ApplicabilityDecision.set_key == set_key).order_by(ApplicabilityDecision.created_at)).scalars().all()
    return [{"id": d.id, "requirement_code": d.requirement_code, "applicable": d.applicable,
             "rationale": d.rationale, "decided_by": S.user_name(db, d.decided_by),
             "created_at": S.iso(d.created_at)} for d in rows]


@router.post("/companies/{company_id}/applicability", status_code=201)
def set_applicability(company_id: str, body: ApplicabilityIn,
                      principal: Principal = Depends(require_roles(*WRITE_ROLES)), db: Session = Depends(get_db)) -> dict:
    c = S.company_or_404(db, principal.org_id, company_id)
    d = ApplicabilityDecision(org_id=principal.org_id, company_id=c.id, set_key=body.set_key,
                              requirement_code=body.requirement_code, applicable=body.applicable,
                              rationale=body.rationale.strip(), decided_by=principal.user_id)
    db.add(d)
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action="applicability.decided",
                 entity_type="company", entity_id=c.id, data=body.model_dump())
    db.flush()
    return {"id": d.id}


def evidence_usage(db: Session, org_id: str, document_id: str) -> int:
    from veridion.models import Passage

    return int(db.execute(
        select(func.count()).select_from(FindingEvidence).join(Passage, Passage.id == FindingEvidence.passage_id)
        .where(Passage.document_id == document_id, Passage.org_id == org_id)
    ).scalar_one())


__all__ = ["Document", "evidence_usage", "router"]
