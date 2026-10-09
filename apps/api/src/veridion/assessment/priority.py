"""Prioritisation heuristic: P = I × G × U.

I — importance of the requirement (catalogue weight 1–3)
G — size of the evidence gap (0 when supported, 1 when nothing is found)
U — urgency from the reporting deadline

This ranks work; it is not a regulatory score. All components are stored and
shown so users can see why an item ranks highly.
"""

from __future__ import annotations

from datetime import date

IMPORTANCE = {1: 0.4, 2: 0.7, 3: 1.0}
GAP_BY_STATUS = {"supported": 0.0, "not_found": 1.0, "conflicting": 0.8, "human_review": 0.5}


def gap_size(status: str, completeness: float) -> float:
    if status == "partially_supported":
        return round(max(0.1, 1.0 - completeness), 3)
    return GAP_BY_STATUS.get(status, 0.5)


def urgency(deadline: date | None, today: date | None = None) -> tuple[float, str]:
    if deadline is None:
        return 0.5, "No deadline set"
    days = (deadline - (today or date.today())).days
    if days <= 30:
        return 1.0, f"Due in {max(days, 0)} days" if days >= 0 else "Deadline passed"
    if days <= 90:
        return 0.8, f"Due in {days} days"
    if days <= 180:
        return 0.6, f"Due in {days} days"
    return 0.4, f"Due in {days} days"


def priority(importance: int, status: str, completeness: float, deadline: date | None,
             today: date | None = None) -> dict:
    i = IMPORTANCE.get(importance, 0.7)
    g = gap_size(status, completeness)
    u, u_note = urgency(deadline, today)
    p = round(i * g * u, 3)
    return {
        "I": i, "G": g, "U": u, "P": p,
        "explanation": f"Importance {i:.1f} × gap {g:.2f} × urgency {u:.1f} ({u_note}) = {p:.2f}",
    }
