"""Versioned requirement catalogues.

Requirement sets are immutable once loaded: a change to the catalogue creates
a new version, so earlier assessment runs remain reproducible.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veridion.db import Base, utcnow
from veridion.ids import new_id
from veridion.models.types import ID_LEN, JSONType


class RequirementSet(Base):
    __tablename__ = "requirement_sets"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)  # "<key>@<version>"
    key: Mapped[str] = mapped_column(String(80), index=True)
    version: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(300))
    framework: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)
    standards: Mapped[list] = mapped_column(JSONType, default=list)  # [{"name", "url"}]
    effective_from: Mapped[date | None] = mapped_column(default=None)
    effective_to: Mapped[date | None] = mapped_column(default=None)
    effective_rule: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(20), default="draft")  # reviewed | draft
    changelog: Mapped[list] = mapped_column(JSONType, default=list)
    supersedes: Mapped[str | None] = mapped_column(String(120))
    succeeded_by: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    loaded_at: Mapped[datetime] = mapped_column(default=utcnow)

    requirements: Mapped[list[Requirement]] = relationship(
        back_populates="requirement_set", order_by="Requirement.ordinal"
    )


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)  # "<set id>/<code>"
    set_id: Mapped[str] = mapped_column(ForeignKey("requirement_sets.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(40))  # e.g. "305-1"
    display_code: Mapped[str] = mapped_column(String(60))  # e.g. "GRI 305-1"
    title: Mapped[str] = mapped_column(String(300))
    topic: Mapped[str] = mapped_column(String(80))
    summary: Mapped[str] = mapped_column(Text)
    applicability: Mapped[str | None] = mapped_column(Text)
    importance: Mapped[int] = mapped_column(Integer, default=2)  # 1 low · 2 medium · 3 high
    elements: Mapped[list] = mapped_column(JSONType, default=list)
    metric_keys: Mapped[list] = mapped_column(JSONType, default=list)
    search_terms: Mapped[list] = mapped_column(JSONType, default=list)
    related_terms: Mapped[list] = mapped_column(JSONType, default=list)
    source_reference: Mapped[str] = mapped_column(String(300))
    source_url: Mapped[str | None] = mapped_column(String(500))
    ordinal: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str] = mapped_column(String(64))

    requirement_set: Mapped[RequirementSet] = relationship(back_populates="requirements")


class ApplicabilityDecision(Base):
    """A reviewer's decision that a requirement does or does not apply to a company."""

    __tablename__ = "applicability_decisions"
    __table_args__ = (Index("ix_applicability_company_set", "company_id", "set_key"),)

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("apl"))
    org_id: Mapped[str] = mapped_column(String(ID_LEN), index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    set_key: Mapped[str] = mapped_column(String(80))
    requirement_code: Mapped[str] = mapped_column(String(40))
    applicable: Mapped[bool] = mapped_column(default=True)
    rationale: Mapped[str] = mapped_column(Text)
    decided_by: Mapped[str | None] = mapped_column(String(ID_LEN))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
