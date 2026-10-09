"""Assessment runs, findings, evidence links, human reviews and remediation actions."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veridion.db import Base, utcnow
from veridion.ids import new_id
from veridion.models.types import ID_LEN, JSONType

STATUSES = ("supported", "partially_supported", "not_found", "conflicting", "human_review")
REVIEW_DECISIONS = ("accept", "override", "comment")
ACTION_STATUSES = ("open", "in_progress", "blocked", "done", "dismissed")


class AssessmentRun(Base):
    """One reproducible execution: Assessment = f(documents, requirements, rules, model)."""

    __tablename__ = "assessment_runs"
    __table_args__ = (Index("ix_runs_company_created", "company_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("run"))
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    requirement_set_id: Mapped[str] = mapped_column(ForeignKey("requirement_sets.id"))
    mode: Mapped[str] = mapped_column(String(20), default="rules")  # rules | hybrid
    status: Mapped[str] = mapped_column(String(20), default="queued")
    label: Mapped[str | None] = mapped_column(String(200))

    period_label: Mapped[str | None] = mapped_column(String(40))
    period_start: Mapped[date | None] = mapped_column(default=None)
    period_end: Mapped[date | None] = mapped_column(default=None)
    deadline: Mapped[date | None] = mapped_column(default=None)

    pipeline_version: Mapped[str | None] = mapped_column(String(40))
    extraction_version: Mapped[str | None] = mapped_column(String(40))
    rules_version: Mapped[str | None] = mapped_column(String(40))
    prompt_version: Mapped[str | None] = mapped_column(String(40))
    llm_provider: Mapped[str | None] = mapped_column(String(80))
    llm_model: Mapped[str | None] = mapped_column(String(120))
    llm_config: Mapped[dict] = mapped_column(JSONType, default=dict)

    # Documents (id, version, sha256) and requirement hashes used as inputs.
    input_manifest: Mapped[dict] = mapped_column(JSONType, default=dict)
    excluded_requirements: Mapped[list] = mapped_column(JSONType, default=list)
    metrics: Mapped[dict] = mapped_column(JSONType, default=dict)  # timings, tokens, cost
    summary: Mapped[dict] = mapped_column(JSONType, default=dict)  # counts per status
    previous_run_id: Mapped[str | None] = mapped_column(String(ID_LEN))
    job_id: Mapped[str | None] = mapped_column(String(ID_LEN))
    error: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[str | None] = mapped_column(String(ID_LEN))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(default=None)
    finished_at: Mapped[datetime | None] = mapped_column(default=None)

    findings: Mapped[list[Finding]] = relationship(back_populates="run", cascade="all, delete-orphan")


class Finding(Base):
    """The assessment of one requirement within one run."""

    __tablename__ = "findings"
    __table_args__ = (UniqueConstraint("run_id", "requirement_id"),)

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("fnd"))
    org_id: Mapped[str] = mapped_column(String(ID_LEN), index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("assessment_runs.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[str] = mapped_column(String(ID_LEN), index=True)
    requirement_id: Mapped[str] = mapped_column(ForeignKey("requirements.id"))
    requirement_code: Mapped[str] = mapped_column(String(40))

    status: Mapped[str] = mapped_column(String(30))
    completeness: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    rationale: Mapped[str] = mapped_column(Text, default="")
    rules_rationale: Mapped[str] = mapped_column(Text, default="")
    element_results: Mapped[list] = mapped_column(JSONType, default=list)
    missing_elements: Mapped[list] = mapped_column(JSONType, default=list)
    requires_human_review: Mapped[bool] = mapped_column(default=False)
    review_reasons: Mapped[list] = mapped_column(JSONType, default=list)

    method: Mapped[str] = mapped_column(String(20), default="rules")
    rules_status: Mapped[str | None] = mapped_column(String(30))
    llm_status: Mapped[str | None] = mapped_column(String(30))
    llm_output: Mapped[dict | None] = mapped_column(JSONType, default=None)
    citation_check: Mapped[dict] = mapped_column(JSONType, default=dict)
    conflicts: Mapped[list] = mapped_column(JSONType, default=list)
    priority: Mapped[dict] = mapped_column(JSONType, default=dict)
    retrieval: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    run: Mapped[AssessmentRun] = relationship(back_populates="findings")
    evidence: Mapped[list[FindingEvidence]] = relationship(
        back_populates="finding", cascade="all, delete-orphan", order_by="FindingEvidence.rank"
    )


class FindingEvidence(Base):
    __tablename__ = "finding_evidence"

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("fev"))
    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id", ondelete="CASCADE"), index=True)
    passage_id: Mapped[str] = mapped_column(ForeignKey("passages.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # supporting | conflicting | related
    element_keys: Mapped[list] = mapped_column(JSONType, default=list)
    metric_id: Mapped[str | None] = mapped_column(String(ID_LEN))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str | None] = mapped_column(Text)

    finding: Mapped[Finding] = relationship(back_populates="evidence")


class Review(Base):
    """Human correction or confirmation of a finding. Append-only."""

    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("rev"))
    org_id: Mapped[str] = mapped_column(String(ID_LEN), index=True)
    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id", ondelete="CASCADE"), index=True)
    reviewer_id: Mapped[str | None] = mapped_column(String(ID_LEN))
    reviewer_name: Mapped[str | None] = mapped_column(String(200))
    decision: Mapped[str] = mapped_column(String(20))
    previous_status: Mapped[str] = mapped_column(String(30))
    new_status: Mapped[str | None] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Action(Base):
    """A remediation task linked to the gap (requirement element) that triggered it."""

    __tablename__ = "actions"
    __table_args__ = (Index("ix_actions_company_gap", "company_id", "requirement_code", "gap_key"),)

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("act"))
    org_id: Mapped[str] = mapped_column(String(ID_LEN), index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    finding_id: Mapped[str | None] = mapped_column(String(ID_LEN))
    run_id: Mapped[str | None] = mapped_column(String(ID_LEN))
    set_key: Mapped[str | None] = mapped_column(String(80))
    requirement_code: Mapped[str] = mapped_column(String(40))
    gap_key: Mapped[str] = mapped_column(String(80))  # element key, "conflict:<metric>", or "requirement"
    title: Mapped[str] = mapped_column(String(300))
    detail: Mapped[str] = mapped_column(Text, default="")
    rationale: Mapped[str] = mapped_column(Text, default="")
    owner: Mapped[str | None] = mapped_column(String(200))
    due_date: Mapped[date | None] = mapped_column(default=None)
    effort: Mapped[str] = mapped_column(String(10), default="medium")
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    priority_components: Mapped[dict] = mapped_column(JSONType, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="open")
    depends_on: Mapped[list] = mapped_column(JSONType, default=list)
    # Set when a later run no longer shows this gap; a human still confirms closure.
    gap_closed_run_id: Mapped[str | None] = mapped_column(String(ID_LEN))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
