"""Deterministic assessment: element checks, conflicts, completeness and status.

The rules layer is conservative. It marks an element satisfied only when it can
point to a specific passage (and, for numbers, a typed value for the right
period). It never treats missing evidence as proof of non-compliance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

from veridion.assessment.context import AssessmentContext, MetricView
from veridion.extraction.metrics import METRIC_BY_KEY
from veridion.models import Requirement

CONFLICT_TOLERANCE = 0.01  # 1% relative difference after unit normalisation
EXCLUDED_KINDS = {"heading", "table"}


@lru_cache(maxsize=2048)
def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


@dataclass
class CheckOutcome:
    satisfied: bool | None  # None: element does not apply
    weak: bool = False
    passage_ids: list[str] = field(default_factory=list)
    metric_ids: list[str] = field(default_factory=list)
    note: str = ""
    context_passage_ids: list[str] = field(default_factory=list)


@dataclass
class ElementResult:
    key: str
    label: str
    weight: float
    status: str  # satisfied | missing | not_applicable
    weak: bool = False
    passage_ids: list[str] = field(default_factory=list)
    metric_ids: list[str] = field(default_factory=list)
    note: str = ""
    source: str = "rules"
    context_passage_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "key": self.key, "label": self.label, "weight": self.weight, "status": self.status, "weak": self.weak,
            "passage_ids": self.passage_ids, "metric_ids": self.metric_ids, "note": self.note, "source": self.source,
            "context_passage_ids": self.context_passage_ids,
        }


@dataclass
class Conflict:
    metric_key: str
    label: str
    unit: str
    period_label: str
    low: MetricView
    high: MetricView
    relative_difference: float
    values: list[MetricView]

    def to_dict(self, ctx: AssessmentContext) -> dict:
        def view(m: MetricView) -> dict:
            return {"metric_id": m.id, "passage_id": m.passage_id, "value": m.value, "unit": m.unit,
                    "normalized_value": m.normalized_value, "normalized_unit": m.normalized_unit,
                    "source": ctx.passage_ref(m.passage_id), "method": m.method, "confidence": m.confidence}

        return {
            "metric_key": self.metric_key, "label": self.label, "unit": self.unit, "period": self.period_label,
            "relative_difference": round(self.relative_difference, 4),
            "low": view(self.low), "high": view(self.high), "values": [view(v) for v in self.values],
        }


@dataclass
class RulesResult:
    status: str
    completeness: float
    elements: list[ElementResult]
    conflicts: list[Conflict]
    rationale: str
    confidence: float
    review_reasons: list[str]
    related_passage_ids: list[str]
    retrieval: dict

    @property
    def missing(self) -> list[ElementResult]:
        return [e for e in self.elements if e.status == "missing"]


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def _fmt_value(m: MetricView) -> str:
    value = f"{m.value:,.0f}" if abs(m.value) >= 100 else f"{m.value:,.3g}"
    return f"{value} {m.unit or ''}".strip()


def _check_metric(check: dict, ctx: AssessmentContext) -> CheckOutcome:
    strong = ctx.metrics_for(check.get("metric_keys", []))
    weak_keys = check.get("weak_metric_keys", [])
    weak = ctx.metrics_for(weak_keys) if weak_keys else []
    found, is_weak = (strong, False) if strong else (weak, bool(weak))
    if found:
        best = found[0]
        passages = list(dict.fromkeys(m.passage_id for m in found))[:3]
        note = f"{_fmt_value(best)} for {ctx.period.label} ({ctx.passage_ref(best.passage_id)})"
        if is_weak:
            note += "; the Scope 2 method is not stated" if "ghg_scope2" in weak_keys else "; weaker match"
        return CheckOutcome(True, is_weak, passages, [m.id for m in found[:5]], note)
    others = [m for m in ctx.metrics_any_period(check.get("metric_keys", []) + weak_keys) if not m.is_base_year]
    if others:
        periods = sorted({m.period_label or "unknown period" for m in others})
        return CheckOutcome(False, note=f"Values found only for other periods: {', '.join(periods)}",
                            passage_ids=list(dict.fromkeys(m.passage_id for m in others))[:2])
    return CheckOutcome(False, note="No value found in the documents assessed")


def _check_metric_period(check: dict, ctx: AssessmentContext) -> CheckOutcome:
    found = ctx.metrics_for(check.get("metric_keys", []))
    if not found:
        return CheckOutcome(False, note=f"No value found for {ctx.period.label}")
    explicit = [m for m in found if not m.period_inferred]
    if explicit:
        m = explicit[0]
        return CheckOutcome(True, False, [m.passage_id], [m.id],
                            f"Period stated with the value: {m.period_label} ({ctx.passage_ref(m.passage_id)})")
    m = found[0]
    return CheckOutcome(True, True, [m.passage_id], [m.id],
                        "Period inferred from the document's stated reporting period, not next to the value")


def _check_pattern(check: dict, ctx: AssessmentContext, relevance: dict[str, float]) -> CheckOutcome:
    patterns = [_rx(p) for p in check.get("patterns", [])]
    context = [_rx(c) for c in check.get("context", [])]
    candidates: list[tuple[float, int, str, str]] = []
    for order, pid in enumerate(ctx.ordered_passage_ids):
        passage = ctx.passages[pid]
        if passage.kind in EXCLUDED_KINDS:
            continue
        text = passage.text
        match = next((m for rx in patterns if (m := rx.search(text))), None)
        if match is None:
            continue
        if context:
            scope = f"{text} {passage.section or ''}"
            if not any(c.search(scope) for c in context):
                continue
        start = max(0, match.start() - 60)
        snippet = text[start: match.end() + 60].strip()
        candidates.append((relevance.get(pid, 0.0), -order, pid, snippet))
    if not candidates:
        return CheckOutcome(False, note="No matching disclosure found")
    candidates.sort(reverse=True)
    best = candidates[0]
    prefix = "…" if not ctx.passages[best[2]].text.startswith(best[3]) else ""
    return CheckOutcome(True, False, [c[2] for c in candidates[:3]],
                        note=f"“{prefix}{best[3]}…” ({ctx.passage_ref(best[2])})")


def evaluate_check(check: dict, ctx: AssessmentContext, relevance: dict[str, float]) -> CheckOutcome:
    kind = check["type"]
    if kind == "metric":
        return _check_metric(check, ctx)
    if kind == "metric_period":
        return _check_metric_period(check, ctx)
    if kind == "pattern":
        return _check_pattern(check, ctx, relevance)
    if kind == "any_of":
        outcomes = [evaluate_check(c, ctx, relevance) for c in check.get("checks", [])]
        satisfied = [o for o in outcomes if o.satisfied]
        if satisfied:
            best = min(satisfied, key=lambda o: o.weak)
            return CheckOutcome(True, best.weak, best.passage_ids, best.metric_ids, best.note)
        return CheckOutcome(False, note=outcomes[0].note if outcomes else "")
    if kind == "conditional":
        condition = evaluate_check(check["when"], ctx, relevance)
        if not condition.satisfied:
            return CheckOutcome(None, note="Not applicable: the triggering condition was not found")
        outcome = evaluate_check(check["then"], ctx, relevance)
        outcome.context_passage_ids = condition.passage_ids[:2]
        trigger = condition.note.split(" (")[0]
        outcome.note = f"{outcome.note}. Applies because the documents state: {trigger}"
        return outcome
    raise ValueError(f"Unknown check type {kind!r}")


# ---------------------------------------------------------------------------
# Conflicts
# ---------------------------------------------------------------------------

def detect_conflicts(ctx: AssessmentContext, metric_keys: list[str]) -> list[Conflict]:
    conflicts: list[Conflict] = []
    for key in metric_keys:
        values = [m for m in ctx.metrics_for([key]) if m.normalized_value is not None]
        by_unit: dict[str, list[MetricView]] = {}
        for m in values:
            by_unit.setdefault(m.normalized_unit or "", []).append(m)
        for unit, group in by_unit.items():
            if len(group) < 2:
                continue
            group.sort(key=lambda m: m.normalized_value or 0.0)
            low, high = group[0], group[-1]
            if low.passage_id == high.passage_id or not low.normalized_value:
                continue
            diff = (high.normalized_value - low.normalized_value) / abs(low.normalized_value)
            if diff > CONFLICT_TOLERANCE:
                label = METRIC_BY_KEY[key].label if key in METRIC_BY_KEY else key
                conflicts.append(Conflict(key, label, unit, ctx.period.label, low, high, diff, group))
    return conflicts


# ---------------------------------------------------------------------------
# Requirement assessment
# ---------------------------------------------------------------------------

def retrieve(requirement: Requirement, ctx: AssessmentContext, limit: int = 8):
    assert ctx.index is not None
    query = " ".join([requirement.title, requirement.summary, *requirement.search_terms])
    return ctx.index.search(
        query, phrases=list(requirement.search_terms), metric_keys=set(requirement.metric_keys),
        section_terms=[requirement.topic, *requirement.search_terms[:3]], limit=limit,
    )


def completeness(elements: list[ElementResult]) -> float:
    applicable = [e for e in elements if e.status != "not_applicable"]
    total = sum(e.weight for e in applicable)
    if total == 0:
        return 0.0
    return round(sum(e.weight for e in applicable if e.status == "satisfied") / total, 4)


def status_from(elements: list[ElementResult], conflicts: list[Conflict]) -> str:
    if conflicts:
        return "conflicting"
    c = completeness(elements)
    if c >= 0.9999:
        return "supported"
    if c > 0:
        return "partially_supported"
    return "not_found"


def assess_requirement(requirement: Requirement, ctx: AssessmentContext) -> RulesResult:
    hits = retrieve(requirement, ctx)
    relevance = {h.id: h.score for h in hits}
    elements: list[ElementResult] = []
    for spec in requirement.elements:
        outcome = evaluate_check(spec["check"], ctx, relevance)
        status = "not_applicable" if outcome.satisfied is None else ("satisfied" if outcome.satisfied else "missing")
        elements.append(ElementResult(
            key=spec["key"], label=spec["label"], weight=float(spec.get("weight", 1)), status=status,
            weak=outcome.weak, passage_ids=outcome.passage_ids if status == "satisfied" else [],
            metric_ids=outcome.metric_ids, note=outcome.note, context_passage_ids=outcome.context_passage_ids,
        ))
    conflicts = detect_conflicts(ctx, list(requirement.metric_keys))
    status = status_from(elements, conflicts)
    c = completeness(elements)

    review_reasons: list[str] = []
    for conflict in conflicts:
        review_reasons.append(
            f"Conflicting values for {conflict.label} ({conflict.period_label}): a reviewer must confirm which "
            "figure is authoritative."
        )
    ocr_keys = [e for e in elements if e.status == "satisfied" and e.passage_ids and all(
        ctx.passages[p].extraction_method == "ocr" for p in e.passage_ids)]
    for e in ocr_keys:
        low_conf = min(ctx.passages[p].confidence for p in e.passage_ids)
        if low_conf < 0.85:
            review_reasons.append(f"“{e.label}” relies on OCR text with confidence {low_conf:.2f}.")
            status = "human_review" if status != "conflicting" else status

    satisfied_ids = {pid for e in elements for pid in e.passage_ids}
    conflict_ids = {v.passage_id for cf in conflicts for v in cf.values}
    related = [h.id for h in hits if h.id not in satisfied_ids and h.id not in conflict_ids][:3]

    confidence = _confidence(elements, conflicts, ctx)
    rationale = build_rationale(status, c, elements, conflicts, ctx, related)
    retrieval = {"hits": [{"passage_id": h.id, **h.explanation()} for h in hits]}
    return RulesResult(status, c, elements, conflicts, rationale, confidence, review_reasons, related, retrieval)


def _confidence(elements: list[ElementResult], conflicts: list[Conflict], ctx: AssessmentContext) -> float:
    applicable = [e for e in elements if e.status != "not_applicable"]
    if not applicable:
        return 0.3
    scores = []
    for e in applicable:
        if e.status == "missing":
            scores.append(0.75)  # absence is checked across every passage, but wording may differ
            continue
        evidence_conf = max((ctx.passages[p].confidence for p in e.passage_ids if p in ctx.passages), default=0.8)
        scores.append(evidence_conf * (0.8 if e.weak else 1.0))
    value = sum(scores) / len(scores)
    if conflicts:
        value *= 0.85
    return round(min(0.95, value), 2)


def _lc(label: str) -> str:
    """Sentence-case a label inside a sentence without mangling acronyms (CO2, GHG)."""
    return label if label[:2].isupper() else label[:1].lower() + label[1:]


def build_rationale(status: str, c: float, elements: list[ElementResult], conflicts: list[Conflict],
                    ctx: AssessmentContext, related: list[str]) -> str:
    applicable = [e for e in elements if e.status != "not_applicable"]
    satisfied = [e for e in applicable if e.status == "satisfied"]
    missing = [e for e in applicable if e.status == "missing"]
    docs = len(ctx.documents)
    parts: list[str] = []
    if status == "conflicting":
        for cf in conflicts:
            parts.append(
                f"The documents report different values for {_lc(cf.label)} ({cf.period_label}): "
                f"{_fmt_value(cf.low)} ({ctx.passage_ref(cf.low.passage_id)}) and "
                f"{_fmt_value(cf.high)} ({ctx.passage_ref(cf.high.passage_id)}), a "
                f"{cf.relative_difference:.1%} difference after converting to {cf.unit}."
            )
        parts.append("A reviewer must confirm which figure is correct before the disclosure can be relied on.")
    elif status == "supported":
        parts.append(f"All {len(applicable)} applicable elements are evidenced in the documents assessed.")
    elif status in ("partially_supported", "human_review") and satisfied:
        parts.append(f"{len(satisfied)} of {len(applicable)} applicable elements are evidenced "
                     f"({c:.0%} of the weighted requirement).")
    elif status == "not_found":
        parts.append(
            f"None of the required elements were found in the {docs} document{'s' if docs != 1 else ''} assessed. "
            "This does not establish non-compliance: the evidence may exist in documents not yet provided."
        )
        if related:
            parts.append(f"{len(related)} related passage{'s' if len(related) != 1 else ''} "
                         "are listed for review.")
    if missing and status != "not_found":
        parts.append("Missing: " + "; ".join(_lc(e.label) for e in missing) + ".")
    weak = [e for e in satisfied if e.weak]
    if weak:
        parts.append("Weaker evidence: " + "; ".join(f"{_lc(e.label)} ({e.note.split(';')[-1].strip()})"
                                                     for e in weak) + ".")
    na = [e for e in elements if e.status == "not_applicable"]
    if na:
        parts.append("Not applicable: " + "; ".join(_lc(e.label) for e in na) + ".")
    return " ".join(parts)
