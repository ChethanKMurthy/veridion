"""Combine deterministic and model assessments into one finding.

Policy (documented in docs/methodology.md):

* Structured elements (numbers, units, periods) are decided by the rules layer.
  If the model disagrees, the finding is flagged for review rather than changed.
* Semantic elements (wording such as boundaries or methodologies) may be
  downgraded by the model when matched wording does not establish them, or
  upgraded when the model cites a valid passage that the patterns missed.
* Conflicts detected across sources can never be overridden by the model.
* Every override is recorded on the element with its source.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from veridion.assessment.llm import LLMAssessment
from veridion.assessment.rules import ElementResult, RulesResult, completeness, status_from
from veridion.models import Requirement

_RANK = {"not_found": 0, "partially_supported": 1, "supported": 2}


def _check_kinds(check: dict) -> set[str]:
    kinds = {check["type"]}
    for nested in check.get("checks", []):
        kinds |= _check_kinds(nested)
    for key in ("when", "then"):
        if check.get(key):
            kinds |= _check_kinds(check[key])
    return kinds


def is_structured(spec: dict) -> bool:
    kinds = _check_kinds(spec["check"]) - {"any_of", "conditional"}
    return bool(kinds) and kinds <= {"metric", "metric_period"}


@dataclass
class Merged:
    status: str
    completeness: float
    elements: list[ElementResult]
    rationale: str
    confidence: float
    review_reasons: list[str]
    requires_human_review: bool
    related_passage_ids: list[str] = field(default_factory=list)
    model_overrides: list[dict] = field(default_factory=list)


def rules_only(rules: RulesResult) -> Merged:
    return Merged(
        status=rules.status, completeness=rules.completeness, elements=rules.elements,
        rationale=rules.rationale, confidence=rules.confidence, review_reasons=list(rules.review_reasons),
        requires_human_review=bool(rules.review_reasons) or rules.status in ("conflicting", "human_review"),
        related_passage_ids=rules.related_passage_ids,
    )


def merge(requirement: Requirement, rules: RulesResult, model: LLMAssessment) -> Merged:
    specs = {s["key"]: s for s in requirement.elements}
    review = list(rules.review_reasons)
    overrides: list[dict] = []
    elements: list[ElementResult] = []

    for element in rules.elements:
        merged = ElementResult(**{**element.__dict__})
        judgement = model.judgements.get(element.key)
        if element.status == "not_applicable" or judgement is None:
            elements.append(merged)
            continue
        structured = is_structured(specs[element.key])
        if judgement.verdict == "no" and element.status == "satisfied":
            if structured:
                review.append(f"The model questioned “{element.label}”: {judgement.note}")
            else:
                merged.status, merged.source = "missing", "model"
                merged.note = f"Model: {judgement.note} (pattern match: {element.note})"
                merged.passage_ids = []
                overrides.append({"element": element.key, "from": "satisfied", "to": "missing",
                                  "reason": judgement.note})
        elif judgement.verdict == "yes" and element.status == "missing":
            if judgement.evidence_ids:
                merged.status, merged.source, merged.weak = "satisfied", "model", True
                merged.passage_ids = judgement.evidence_ids[:3]
                merged.note = f"Identified by the model: {judgement.note}"
                overrides.append({"element": element.key, "from": "missing", "to": "satisfied",
                                  "reason": judgement.note})
                if structured:
                    review.append(f"“{element.label}” was identified by the model but not by value extraction; "
                                  "confirm the figure against the source.")
            elif judgement.invalid_ids:
                review.append(f"The model cited evidence that does not exist for “{element.label}”; ignored.")
        elif judgement.verdict == "unclear":
            if structured and model.confidence >= 0.6:
                merged.note = f"{element.note} · Model note: {judgement.note}"
            else:
                review.append(f"The model could not determine “{element.label}”: {judgement.note}")
        elements.append(merged)

    status = status_from(elements, rules.conflicts)
    c = completeness(elements)
    related = list(rules.related_passage_ids)

    if status == "not_found" and model.status == "partially_supported" and model.evidence_ids:
        status = "partially_supported"
        related = list(dict.fromkeys(model.evidence_ids + related))[:4]
        overrides.append({"element": None, "from": "not_found", "to": "partially_supported",
                          "reason": "Related disclosure found, but no required element is established."})

    if model.status in _RANK and status in _RANK and abs(_RANK[model.status] - _RANK[status]) == 2:
        review.append(f"The model's overall view ({model.status.replace('_', ' ')}) differs sharply from the "
                      f"evidence checks ({status.replace('_', ' ')}).")
        status = "human_review"
    if model.status == "conflicting" and status != "conflicting":
        review.append("The model identified a possible contradiction that value checks did not confirm.")
    if model.requires_human_review and model.confidence < 0.5 and status != "conflicting":
        status = "human_review"
        review.append("The model could not resolve this requirement with confidence.")
    if model.invalid_ids:
        review.append(f"{len(set(model.invalid_ids))} citation(s) from the model referred to unknown evidence "
                      "and were discarded.")

    agreement = model.status == status
    confidence = round(min(0.95, (rules.confidence + model.confidence) / 2 * (1.0 if agreement else 0.85)), 2)
    rationale = model.rationale.strip() or rules.rationale
    return Merged(
        status=status, completeness=c, elements=elements, rationale=rationale, confidence=confidence,
        review_reasons=list(dict.fromkeys(review)),
        requires_human_review=bool(review) or status in ("conflicting", "human_review"),
        related_passage_ids=related, model_overrides=overrides,
    )
