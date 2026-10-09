"""Remediation actions linked to the gaps that triggered them.

Actions persist across runs. A later run updates an open action instead of
duplicating it, and marks it as "gap closed" (for a human to confirm) when the
evidence now satisfies the element.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from veridion.models import Action, AssessmentRun, Finding, Requirement


def fmt_value(value: float) -> str:
    """12,345 · 0.82 · 63.4 — never scientific notation."""
    if abs(value) >= 100:
        return f"{value:,.0f}"
    return f"{value:,.3f}".rstrip("0").rstrip(".")


@dataclass
class Gap:
    requirement: Requirement
    finding: Finding
    gap_key: str
    title: str
    detail: str
    rationale: str
    effort: str
    depends_on: list[str]


def gaps_for(finding: Finding, requirement: Requirement) -> list[Gap]:
    if finding.status == "supported":
        return []
    specs = {s["key"]: s for s in requirement.elements}
    gaps: list[Gap] = []
    for conflict in finding.conflicts or []:
        low, high = conflict["low"], conflict["high"]
        gaps.append(Gap(
            requirement, finding, f"conflict:{conflict['metric_key']}",
            f"Reconcile {conflict['label'][:1].lower() + conflict['label'][1:]} for {conflict['period']}",
            f"The documents disagree: {fmt_value(low['value'])} {low['unit']} ({low['source']}) versus "
            f"{fmt_value(high['value'])} {high['unit']} ({high['source']}). Confirm the authoritative figure, "
            "correct or footnote the other document, and record any restatement.",
            f"{conflict['relative_difference']:.1%} difference after unit conversion.", "medium", [],
        ))
    for element in finding.element_results or []:
        if element["status"] != "missing":
            continue
        spec = specs.get(element["key"])
        if spec is None:
            continue
        action = spec.get("action", {})
        gaps.append(Gap(
            requirement, finding, element["key"], action.get("title", f"Provide evidence: {element['label']}"),
            (action.get("detail") or "").strip(), element.get("note", ""), action.get("effort", "medium"),
            list(action.get("depends_on", [])),
        ))
    if finding.status == "human_review" and not gaps:
        gaps.append(Gap(
            requirement, finding, "review", f"Review the assessment of {requirement.display_code}",
            "Inspect the cited evidence and record a review decision on the finding.",
            "; ".join(finding.review_reasons or [])[:500], "low", [],
        ))
    return gaps


def sync_actions(session: Session, run: AssessmentRun, set_key: str,
                 pairs: list[tuple[Finding, Requirement]]) -> dict:
    existing = {
        (a.requirement_code, a.gap_key): a
        for a in session.execute(
            select(Action).where(Action.org_id == run.org_id, Action.company_id == run.company_id,
                                 Action.set_key == set_key)
        ).scalars()
    }
    current: dict[tuple[str, str], Action] = {}
    created = updated = reopened = 0
    for finding, requirement in pairs:
        gaps = gaps_for(finding, requirement)
        for gap in gaps:
            key = (requirement.code, gap.gap_key)
            action = existing.get(key)
            priority = dict(finding.priority or {})
            if action is None:
                action = Action(
                    org_id=run.org_id, company_id=run.company_id, set_key=set_key, requirement_code=requirement.code,
                    gap_key=gap.gap_key, title=gap.title, detail=gap.detail, rationale=gap.rationale,
                    effort=gap.effort, status="open",
                )
                session.add(action)
                created += 1
            else:
                updated += 1
                if action.status == "done":
                    action.status = "open"
                    reopened += 1
                action.title, action.detail, action.rationale = gap.title, gap.detail, gap.rationale
            action.finding_id, action.run_id = finding.id, run.id
            action.priority_score = float(priority.get("P", 0.0))
            action.priority_components = priority
            action.gap_closed_run_id = None
            action.depends_on = [f"{requirement.code}:{d}" for d in gap.depends_on]
            current[key] = action
    closed = 0
    for key, action in existing.items():
        if key not in current and action.status not in ("done", "dismissed") and action.gap_closed_run_id is None:
            requirement_codes = {r.code for _, r in pairs}
            if action.requirement_code in requirement_codes:
                action.gap_closed_run_id = run.id
                closed += 1
    session.flush()
    # Resolve "<code>:<element>" dependencies into action ids where the dependency is itself open.
    by_gap = {f"{code}:{gap}": a.id for (code, gap), a in current.items()}
    for action in current.values():
        action.depends_on = [by_gap[d] for d in action.depends_on if d in by_gap]
    return {"created": created, "updated": updated, "reopened": reopened, "gap_closed": closed}
