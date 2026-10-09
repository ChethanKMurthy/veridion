"""Public endpoints: health checks and website enquiries."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from veridion import __version__
from veridion.api.deps import Principal, client_ip, rate_limiter, require_platform_admin
from veridion.api.serializers import iso
from veridion.api.types import Email
from veridion.db import get_db
from veridion.ids import sha256_text
from veridion.models import Enquiry, Organization
from veridion.services import audit
from veridion.services.entitlements import PLANS

router = APIRouter(tags=["public"])

ENQUIRY_KINDS = ("demo_request", "access_request", "sales", "enterprise", "support", "billing", "security",
                 "privacy", "media", "partnership", "accessibility", "complaint", "general")


class EnquiryIn(BaseModel):
    kind: str = Field(pattern="^(" + "|".join(ENQUIRY_KINDS) + ")$")
    name: str = Field(min_length=1, max_length=200)
    email: Email
    organization: str | None = Field(default=None, max_length=200)
    subject: str | None = Field(default=None, max_length=300)
    message: str = Field(min_length=10, max_length=8000)
    reference: str | None = Field(default=None, max_length=120)  # product version or assessment id
    website: str | None = None  # honeypot: must stay empty


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@router.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ready"}


@router.post("/public/enquiries", status_code=201)
def submit_enquiry(body: EnquiryIn, request: Request, db: Session = Depends(get_db)) -> dict:
    ip = client_ip(request)
    rate_limiter.check(f"enquiry:{ip}", 5, 600)
    if body.website:  # bots fill hidden fields; accept silently, store nothing
        return {"received": True, "reference": "ENQ-IGNORED"}
    enquiry = Enquiry(kind=body.kind, name=body.name.strip(), email=body.email.lower(),
                      organization=(body.organization or "").strip() or None, subject=body.subject,
                      message=body.message.strip(),
                      context={"reference": body.reference, "ip_hash": sha256_text(ip)[:16],
                               "user_agent": request.headers.get("user-agent", "")[:200]})
    db.add(enquiry)
    db.flush()
    return {"received": True, "reference": enquiry.id.upper().replace("ENQ_", "ENQ-")[:16]}


# --- platform administration (operators of the Veridion service) -----------------------

class PlanIn(BaseModel):
    plan: str


@router.get("/admin/enquiries")
def list_enquiries(kind: str | None = None, principal: Principal = Depends(require_platform_admin),
                   db: Session = Depends(get_db)) -> list[dict]:
    q = select(Enquiry).order_by(Enquiry.created_at.desc()).limit(200)
    if kind:
        q = q.where(Enquiry.kind == kind)
    return [{"id": e.id, "kind": e.kind, "name": e.name, "email": e.email, "organization": e.organization,
             "subject": e.subject, "message": e.message, "context": e.context, "status": e.status,
             "created_at": iso(e.created_at)} for e in db.execute(q).scalars()]


@router.get("/admin/organizations")
def list_orgs(principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)) -> list[dict]:
    return [{"id": o.id, "name": o.name, "plan": o.plan, "is_demo": o.is_demo, "created_at": iso(o.created_at)}
            for o in db.execute(select(Organization).order_by(Organization.created_at.desc())).scalars()]


@router.patch("/admin/organizations/{org_id}/plan")
def set_plan(org_id: str, body: PlanIn, principal: Principal = Depends(require_platform_admin),
             db: Session = Depends(get_db)) -> dict:
    org = db.get(Organization, org_id)
    if org is None:
        raise HTTPException(404, "Organization not found")
    if body.plan not in PLANS:
        raise HTTPException(422, f"plan must be one of {', '.join(PLANS)}")
    previous, org.plan = org.plan, body.plan
    audit.record(db, org_id=org.id, actor_id=principal.user_id, action="org.plan_changed",
                 entity_type="organization", entity_id=org.id, data={"from": previous, "to": body.plan})
    return {"id": org.id, "plan": org.plan}
