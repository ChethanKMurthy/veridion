"""Tenancy, identity, audit and commercial records."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veridion.db import Base, utcnow
from veridion.ids import new_id
from veridion.models.types import ID_LEN, JSONType

ROLES = ("owner", "admin", "analyst", "reviewer", "viewer")


class Organization(Base):
    """A tenant: a consultancy, research team or company. All data is scoped to one."""

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("org"))
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    plan: Mapped[str] = mapped_column(String(32), default="explorer")
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    memberships: Mapped[list[Membership]] = relationship(back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("usr"))
    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(300))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(default=None)

    memberships: Mapped[list[Membership]] = relationship(back_populates="user")


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("org_id", "user_id"),)

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("mem"))
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20), default="analyst")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    organization: Mapped[Organization] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")


class AuditEvent(Base):
    """Append-only record of security- and assessment-relevant actions."""

    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_events_org_created", "org_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("aud"))
    org_id: Mapped[str | None] = mapped_column(String(ID_LEN), index=False)
    actor_id: Mapped[str | None] = mapped_column(String(ID_LEN))
    action: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str | None] = mapped_column(String(40))
    entity_id: Mapped[str | None] = mapped_column(String(ID_LEN))
    data: Mapped[dict] = mapped_column(JSONType, default=dict)
    ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class UsageEvent(Base):
    """Metered usage, the basis for plan limits and future billing."""

    __tablename__ = "usage_events"
    __table_args__ = (Index("ix_usage_events_org_kind_created", "org_id", "kind", "created_at"),)

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("use"))
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(40))
    quantity: Mapped[float] = mapped_column(default=1.0)
    ref_id: Mapped[str | None] = mapped_column(String(ID_LEN))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Enquiry(Base):
    """Submissions from the public website (demo requests, support, security reports…)."""

    __tablename__ = "enquiries"

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("enq"))
    kind: Mapped[str] = mapped_column(String(40), index=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320))
    organization: Mapped[str | None] = mapped_column(String(200))
    subject: Mapped[str | None] = mapped_column(String(300))
    message: Mapped[str] = mapped_column(Text)
    context: Mapped[dict] = mapped_column(JSONType, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="new")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
