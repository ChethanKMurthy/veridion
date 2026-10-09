"""Registration, sign-in, sessions and organization membership."""

from __future__ import annotations

import re
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from veridion.api.deps import ADMIN_ROLES, Principal, client_ip, get_principal, rate_limiter, require_roles
from veridion.api.errors import RegistrationClosed
from veridion.api.serializers import iso
from veridion.api.types import Email
from veridion.config import get_settings
from veridion.db import get_db, utcnow
from veridion.models import AuditEvent, Membership, Organization, User
from veridion.models.identity import ROLES
from veridion.security import create_session_token, dummy_verify, hash_password, verify_password
from veridion.services import audit, entitlements

router = APIRouter(tags=["auth"])


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: Email
    password: str = Field(min_length=10, max_length=200)
    organization: str = Field(min_length=2, max_length=200)


class LoginIn(BaseModel):
    email: Email
    password: str = Field(min_length=1, max_length=200)
    organization_id: str | None = None


class SwitchIn(BaseModel):
    organization_id: str


def _slugify(name: str, db: Session) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60] or "org"
    slug, n = base, 1
    while db.execute(select(Organization.id).where(Organization.slug == slug)).first():
        n += 1
        slug = f"{base}-{n}"
    return slug


def _set_cookie(response: Response, token: str) -> None:
    s = get_settings()
    response.set_cookie(s.session_cookie_name, token, max_age=s.session_ttl_hours * 3600, httponly=True,
                        secure=s.cookie_secure, samesite="lax", path="/")


def me_payload(db: Session, user: User, org: Organization, role: str) -> dict:
    memberships = db.execute(select(Membership).where(Membership.user_id == user.id)).scalars().all()
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email, "created_at": iso(user.created_at)},
        "organization": {"id": org.id, "name": org.name, "slug": org.slug, "plan": org.plan, "is_demo": org.is_demo},
        "role": role,
        "memberships": [{"organization_id": m.org_id, "organization": m.organization.name, "role": m.role}
                        for m in memberships],
        "is_platform_admin": user.email.lower() in get_settings().admin_emails,
    }


@router.post("/auth/register", status_code=201)
def register(body: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    if not get_settings().allow_registration:
        raise RegistrationClosed("New workspaces are by invitation while Veridion is in its pilot phase.")
    rate_limiter.check(f"register:{client_ip(request)}", 5, 3600)
    email = body.email.lower()
    if db.execute(select(User.id).where(User.email == email)).first():
        raise HTTPException(409, "An account with this email already exists. Sign in instead.")
    org = Organization(name=body.organization.strip(), slug=_slugify(body.organization, db), plan="explorer")
    user = User(email=email, name=body.name.strip(), password_hash=hash_password(body.password))
    db.add_all([org, user])
    db.flush()
    db.add(Membership(org_id=org.id, user_id=user.id, role="owner"))
    audit.record(db, org_id=org.id, actor_id=user.id, action="org.created", entity_type="organization",
                 entity_id=org.id, ip=client_ip(request))
    db.flush()
    _set_cookie(response, create_session_token(user.id, org.id))
    return me_payload(db, user, org, "owner")


@router.post("/auth/login")
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    email = body.email.lower()
    rate_limiter.check(f"login:{client_ip(request)}:{email}", 10, 300)
    # Per-account ceiling as well, so rotating source addresses does not allow unlimited guesses.
    rate_limiter.check(f"login-account:{email}", 30, 900)
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        dummy_verify(body.password)
        raise HTTPException(401, "Email or password is incorrect.")
    if not verify_password(body.password, user.password_hash) or not user.is_active:
        audit.record(db, org_id=None, actor_id=user.id, action="auth.login_failed", ip=client_ip(request))
        raise HTTPException(401, "Email or password is incorrect.")
    q = select(Membership).where(Membership.user_id == user.id)
    if body.organization_id:
        q = q.where(Membership.org_id == body.organization_id)
    membership = db.execute(q.order_by(Membership.created_at)).scalars().first()
    if membership is None:
        raise HTTPException(403, "This account is not a member of any organization.")
    user.last_login_at = utcnow()
    audit.record(db, org_id=membership.org_id, actor_id=user.id, action="auth.login", ip=client_ip(request))
    _set_cookie(response, create_session_token(user.id, membership.org_id))
    return me_payload(db, user, membership.organization, membership.role)


@router.post("/auth/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(get_settings().session_cookie_name, path="/")
    return {"ok": True}


@router.get("/auth/me")
def me(principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> dict:
    return me_payload(db, principal.user, principal.org, principal.role)


@router.post("/auth/switch-organization")
def switch_org(body: SwitchIn, response: Response, principal: Principal = Depends(get_principal),
               db: Session = Depends(get_db)) -> dict:
    membership = db.execute(select(Membership).where(Membership.user_id == principal.user_id,
                                                     Membership.org_id == body.organization_id)).scalar_one_or_none()
    if membership is None:
        raise HTTPException(404, "Organization not found")
    _set_cookie(response, create_session_token(principal.user_id, membership.org_id))
    return me_payload(db, principal.user, membership.organization, membership.role)


# --- organization -------------------------------------------------------------

class OrgPatch(BaseModel):
    name: str = Field(min_length=2, max_length=200)


class MemberIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: Email
    role: str = "analyst"


class MemberPatch(BaseModel):
    role: str


@router.get("/org")
def get_org(principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> dict:
    org = principal.org
    details = entitlements.describe(db, org.id)
    return {"id": org.id, "name": org.name, "slug": org.slug, "plan": org.plan, "is_demo": org.is_demo,
            "created_at": iso(org.created_at), "plan_details": details["plan"], "usage": details["usage"],
            "llm_available": get_settings().llm_enabled}


@router.patch("/org")
def patch_org(body: OrgPatch, principal: Principal = Depends(require_roles(*ADMIN_ROLES)),
              db: Session = Depends(get_db)) -> dict:
    principal.org.name = body.name.strip()
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action="org.renamed",
                 entity_type="organization", entity_id=principal.org_id, data={"name": body.name})
    return {"id": principal.org.id, "name": principal.org.name}


@router.get("/org/members")
def members(principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(Membership).where(Membership.org_id == principal.org_id)
                      .order_by(Membership.created_at)).scalars().all()
    return [{"id": m.id, "user_id": m.user_id, "name": m.user.name, "email": m.user.email, "role": m.role,
             "created_at": iso(m.created_at), "last_login_at": iso(m.user.last_login_at)} for m in rows]


@router.post("/org/members", status_code=201)
def add_member(body: MemberIn, principal: Principal = Depends(require_roles(*ADMIN_ROLES)),
               db: Session = Depends(get_db)) -> dict:
    if body.role not in ROLES or body.role == "owner":
        raise HTTPException(400, "Role must be admin, analyst, reviewer or viewer.")
    entitlements.check_seat_quota(db, principal.org_id)
    email = body.email.lower()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    temporary_password = None
    if user is None:
        temporary_password = secrets.token_urlsafe(12)
        user = User(email=email, name=body.name.strip(), password_hash=hash_password(temporary_password))
        db.add(user)
        db.flush()
    elif db.execute(select(Membership.id).where(Membership.org_id == principal.org_id,
                                                Membership.user_id == user.id)).first():
        raise HTTPException(409, "This person is already a member.")
    membership = Membership(org_id=principal.org_id, user_id=user.id, role=body.role)
    db.add(membership)
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action="member.added",
                 entity_type="user", entity_id=user.id, data={"role": body.role, "email": email})
    db.flush()
    return {"id": membership.id, "user_id": user.id, "email": email, "role": body.role,
            "temporary_password": temporary_password}


@router.patch("/org/members/{membership_id}")
def patch_member(membership_id: str, body: MemberPatch, principal: Principal = Depends(require_roles(*ADMIN_ROLES)),
                 db: Session = Depends(get_db)) -> dict:
    m = db.get(Membership, membership_id)
    if m is None or m.org_id != principal.org_id:
        raise HTTPException(404, "Member not found")
    if body.role not in ROLES:
        raise HTTPException(400, "Unknown role")
    if m.role == "owner" and body.role != "owner":
        owners = db.execute(select(Membership).where(Membership.org_id == principal.org_id,
                                                     Membership.role == "owner")).scalars().all()
        if len(owners) <= 1:
            raise HTTPException(400, "An organization needs at least one owner.")
    if body.role == "owner" and principal.role != "owner":
        raise HTTPException(403, "Only an owner can grant the owner role.")
    m.role = body.role
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action="member.role_changed",
                 entity_type="user", entity_id=m.user_id, data={"role": body.role})
    return {"id": m.id, "role": m.role}


@router.delete("/org/members/{membership_id}")
def remove_member(membership_id: str, principal: Principal = Depends(require_roles(*ADMIN_ROLES)),
                  db: Session = Depends(get_db)) -> dict:
    m = db.get(Membership, membership_id)
    if m is None or m.org_id != principal.org_id:
        raise HTTPException(404, "Member not found")
    if m.role == "owner":
        raise HTTPException(400, "Transfer ownership before removing an owner.")
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action="member.removed",
                 entity_type="user", entity_id=m.user_id)
    db.delete(m)
    return {"ok": True}


@router.get("/org/audit-events")
def audit_events(limit: int = 100, principal: Principal = Depends(get_principal),
                 db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(select(AuditEvent).where(AuditEvent.org_id == principal.org_id)
                      .order_by(AuditEvent.created_at.desc()).limit(min(limit, 500))).scalars().all()
    names = {u.id: u.name for u in db.execute(
        select(User).where(User.id.in_({r.actor_id for r in rows if r.actor_id}))).scalars()}
    return [{"id": e.id, "action": e.action, "actor_id": e.actor_id, "actor_name": names.get(e.actor_id or ""),
             "entity_type": e.entity_type, "entity_id": e.entity_id, "data": e.data,
             "created_at": iso(e.created_at)} for e in rows]
