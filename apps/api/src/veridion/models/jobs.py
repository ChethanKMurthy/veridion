"""Background jobs and the LLM response cache."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from veridion.db import Base, utcnow
from veridion.ids import new_id
from veridion.models.types import ID_LEN, JSONType


class Job(Base):
    """A unit of background work. Claimed with SKIP LOCKED on PostgreSQL."""

    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_status_run_after", "status", "run_after"),)

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("job"))
    org_id: Mapped[str | None] = mapped_column(String(ID_LEN), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSONType, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued|running|succeeded|failed
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    run_after: Mapped[datetime] = mapped_column(default=utcnow)
    locked_by: Mapped[str | None] = mapped_column(String(80))
    locked_at: Mapped[datetime | None] = mapped_column(default=None)
    progress: Mapped[dict] = mapped_column(JSONType, default=dict)  # {"stage", "pct", "message"}
    result: Mapped[dict] = mapped_column(JSONType, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(default=None)
    finished_at: Mapped[datetime | None] = mapped_column(default=None)


class LLMCacheEntry(Base):
    """Cached model responses keyed by a hash of model, prompt version and inputs.

    Makes repeated assessments reproducible and avoids paying twice for identical calls.
    """

    __tablename__ = "llm_cache"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    model: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(40))
    response: Mapped[dict] = mapped_column(JSONType)
    usage: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
