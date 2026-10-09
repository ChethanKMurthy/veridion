"""Append-only audit trail."""

from __future__ import annotations

from sqlalchemy.orm import Session

from veridion.models import AuditEvent


def record(session: Session, *, org_id: str | None, actor_id: str | None, action: str,
           entity_type: str | None = None, entity_id: str | None = None, data: dict | None = None,
           ip: str | None = None) -> AuditEvent:
    event = AuditEvent(org_id=org_id, actor_id=actor_id, action=action, entity_type=entity_type,
                       entity_id=entity_id, data=data or {}, ip=ip)
    session.add(event)
    return event
