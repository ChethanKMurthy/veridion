"""Usage metering: the basis for plan limits today and billing later."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from veridion.db import utcnow
from veridion.models import UsageEvent


def record(session: Session, org_id: str, kind: str, quantity: float = 1.0, ref_id: str | None = None) -> None:
    session.add(UsageEvent(org_id=org_id, kind=kind, quantity=quantity, ref_id=ref_id))


def month_start(now: datetime | None = None) -> datetime:
    now = now or utcnow()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def total_since(session: Session, org_id: str, kind: str, since: datetime) -> float:
    return float(session.execute(
        select(func.coalesce(func.sum(UsageEvent.quantity), 0.0))
        .where(UsageEvent.org_id == org_id, UsageEvent.kind == kind, UsageEvent.created_at >= since)
    ).scalar_one())


def summary(session: Session, org_id: str) -> dict:
    since = month_start()
    kinds = ["assessment_runs", "hybrid_runs", "documents_processed", "pages_processed", "llm_tokens"]
    return {kind: total_since(session, org_id, kind, since) for kind in kinds} | {"period_start": since.isoformat()}
