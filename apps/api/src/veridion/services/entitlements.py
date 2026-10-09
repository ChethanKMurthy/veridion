"""Plans and the limits they grant.

Plans are configuration, not code paths: adding a tier or changing a limit is a
one-line change here. Limits are enforced server-side and reported to the
interface so customers can see their usage.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from veridion.models import Company, Document, Membership, Organization
from veridion.services import usage


class PlanLimitError(Exception):
    """Raised when an action would exceed the organization's plan."""

    def __init__(self, message: str, limit: str) -> None:
        super().__init__(message)
        self.limit = limit


@dataclass(frozen=True)
class Plan:
    key: str
    name: str
    max_companies: int | None
    max_documents: int | None
    max_pages_per_document: int | None
    runs_per_month: int | None
    hybrid_runs_per_month: int | None
    max_seats: int | None
    exports: tuple[str, ...]


PLANS: dict[str, Plan] = {
    "explorer": Plan("explorer", "Explorer", max_companies=3, max_documents=10, max_pages_per_document=150,
                     runs_per_month=15, hybrid_runs_per_month=3, max_seats=1, exports=("json", "csv", "md")),
    "professional": Plan("professional", "Professional", max_companies=50, max_documents=500,
                         max_pages_per_document=600, runs_per_month=300, hybrid_runs_per_month=150, max_seats=5,
                         exports=("json", "csv", "md")),
    "enterprise": Plan("enterprise", "Enterprise", max_companies=None, max_documents=None,
                       max_pages_per_document=None, runs_per_month=None, hybrid_runs_per_month=None,
                       max_seats=None, exports=("json", "csv", "md")),
}


def plan_for(session: Session, org_id: str) -> Plan:
    org = session.get(Organization, org_id)
    return PLANS.get(org.plan if org else "explorer", PLANS["explorer"])


def _count(session: Session, stmt) -> int:
    return int(session.execute(stmt).scalar_one())


def check_company_quota(session: Session, org_id: str) -> None:
    plan = plan_for(session, org_id)
    if plan.max_companies is None:
        return
    n = _count(session, select(func.count()).select_from(Company).where(Company.org_id == org_id))
    if n >= plan.max_companies:
        raise PlanLimitError(f"The {plan.name} plan includes up to {plan.max_companies} companies.", "companies")


def check_document_quota(session: Session, org_id: str) -> None:
    plan = plan_for(session, org_id)
    if plan.max_documents is None:
        return
    n = _count(session, select(func.count()).select_from(Document)
               .where(Document.org_id == org_id, Document.superseded_at.is_(None)))
    if n >= plan.max_documents:
        raise PlanLimitError(f"The {plan.name} plan includes up to {plan.max_documents} documents.", "documents")


def check_page_limit(session: Session, org_id: str, pages: int) -> None:
    plan = plan_for(session, org_id)
    if plan.max_pages_per_document is not None and pages > plan.max_pages_per_document:
        raise PlanLimitError(
            f"Documents on the {plan.name} plan are limited to {plan.max_pages_per_document} pages "
            f"(this one has {pages}).", "pages")


def check_run_quota(session: Session, org_id: str, hybrid: bool) -> None:
    plan = plan_for(session, org_id)
    since = usage.month_start()
    if plan.runs_per_month is not None and usage.total_since(session, org_id, "assessment_runs", since) >= plan.runs_per_month:
        raise PlanLimitError(f"The {plan.name} plan includes {plan.runs_per_month} assessment runs per month.", "runs")
    if hybrid and plan.hybrid_runs_per_month is not None and \
            usage.total_since(session, org_id, "hybrid_runs", since) >= plan.hybrid_runs_per_month:
        raise PlanLimitError(
            f"The {plan.name} plan includes {plan.hybrid_runs_per_month} AI-assisted runs per month. "
            "Rules-only runs remain available.", "hybrid_runs")


def check_seat_quota(session: Session, org_id: str) -> None:
    plan = plan_for(session, org_id)
    if plan.max_seats is None:
        return
    n = _count(session, select(func.count()).select_from(Membership).where(Membership.org_id == org_id))
    if n >= plan.max_seats:
        raise PlanLimitError(f"The {plan.name} plan includes {plan.max_seats} seat(s).", "seats")


def describe(session: Session, org_id: str) -> dict:
    plan = plan_for(session, org_id)
    return {"plan": asdict(plan), "usage": usage.summary(session, org_id)}
