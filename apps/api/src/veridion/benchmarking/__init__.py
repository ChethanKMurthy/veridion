"""Peer benchmarking with explicit comparability checks.

Values are only compared after unit normalisation, and every comparison lists
what makes it imperfect: different fiscal periods, consolidation approaches,
Scope 2 methods, OCR-derived values, or conflicting figures within a company's
own documents. A missing value is reported as "not disclosed", never as zero.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from veridion.assessment.context import AssessmentContext, MetricView, period_matches, short_doc_name
from veridion.assessment.rules import CONFLICT_TOLERANCE
from veridion.extraction.metrics import METRIC_BY_KEY
from veridion.extraction.periods import Period, describe, fiscal_year
from veridion.models import Company, Document, Passage
from veridion.services.documents import current_documents


@dataclass(frozen=True)
class BenchmarkMetric:
    key: str
    label: str
    unit: str
    question: str
    lower_is_better: bool | None = None


BENCHMARK_METRICS: tuple[BenchmarkMetric, ...] = (
    BenchmarkMetric("ghg_scope1", "Scope 1 emissions", "tCO2e", "How large are direct emissions?", True),
    BenchmarkMetric("ghg_scope2_location", "Scope 2 emissions (location-based)", "tCO2e",
                    "How large are electricity-related emissions on a grid-average basis?", True),
    BenchmarkMetric("ghg_scope2_market", "Scope 2 emissions (market-based)", "tCO2e",
                    "What are electricity emissions after contractual instruments?", True),
    BenchmarkMetric("ghg_scope3", "Scope 3 emissions", "tCO2e", "Are value-chain emissions quantified?", True),
    BenchmarkMetric("ghg_intensity", "GHG intensity", "tCO2e per unit", "How efficient is production?", True),
    BenchmarkMetric("energy_total", "Total energy consumption", "MWh", "How much energy is consumed?", True),
    BenchmarkMetric("energy_renewable_share", "Renewable share", "%", "How much energy or electricity is renewable?",
                    False),
    BenchmarkMetric("water_withdrawal", "Water withdrawal", "m3", "How much water is withdrawn?", True),
    BenchmarkMetric("waste_generated", "Waste generated", "t", "How much waste is generated?", True),
    BenchmarkMetric("ltifr", "Lost-time injury frequency rate", "rate", "How safe are operations?", True),
)
FALLBACK_KEYS = {"ghg_scope2_location": "ghg_scope2"}

BOUNDARY_RE = re.compile(r"(operational|financial)[\s-]control|equity[\s-]share", re.IGNORECASE)


def _boundary(ctx: AssessmentContext) -> dict | None:
    for pid in ctx.ordered_passage_ids:
        p = ctx.passages[pid]
        m = BOUNDARY_RE.search(p.text)
        if m and re.search(r"emission|ghg|greenhouse|scope|report", p.text, re.IGNORECASE):
            label = m.group(0).lower().replace("-", " ")
            return {"approach": label, "passage_id": pid, "source": ctx.passage_ref(pid)}
    return None


def _value_view(m: MetricView, ctx: AssessmentContext, session: Session) -> dict:
    passage = ctx.passages.get(m.passage_id)
    doc = ctx.documents.get(m.document_id)
    return {
        "metric_id": m.id, "value": m.value, "unit": m.unit, "normalized_value": m.normalized_value,
        "normalized_unit": m.normalized_unit, "period_label": m.period_label,
        "period_start": m.period_start.isoformat() if m.period_start else None,
        "period_end": m.period_end.isoformat() if m.period_end else None,
        "passage_id": m.passage_id, "document_id": m.document_id,
        "document_title": doc.title if doc else None, "source": f"{short_doc_name(doc)}, p.{passage.page}" if doc and passage else None,
        "page": passage.page if passage else None, "method": m.method, "confidence": m.confidence,
        "qualifiers": m.qualifiers,
    }


def company_period(company: Company, label: str) -> Period:
    year = int(re.sub(r"\D", "", label)[-4:])
    return fiscal_year(year, company.fiscal_year_end)


def benchmark(session: Session, org_id: str, focal: Company, peers: list[Company], period_label: str) -> dict:
    companies = [focal, *peers]
    contexts: dict[str, AssessmentContext] = {}
    periods: dict[str, Period] = {}
    boundaries: dict[str, dict | None] = {}
    for company in companies:
        period = company_period(company, period_label)
        docs = [d for d in current_documents(session, org_id, company.id) if d.status == "ready"]
        ctx = AssessmentContext.load(session, org_id, company.id, docs, period)
        contexts[company.id], periods[company.id] = ctx, period
        boundaries[company.id] = _boundary(ctx)

    focal_period = periods[focal.id]
    rows = []
    for metric in BENCHMARK_METRICS:
        cells = []
        for company in companies:
            ctx = contexts[company.id]
            key = metric.key
            values = ctx.metrics_for([key])
            notes: list[dict] = []
            if not values and key in FALLBACK_KEYS:
                values = ctx.metrics_for([FALLBACK_KEYS[key]])
                if values:
                    notes.append({"kind": "method", "text": "Scope 2 method not stated; shown as location-based "
                                                            "for comparison only."})
            if not values:
                cells.append({"company_id": company.id, "status": "not_disclosed", "value": None,
                              "notes": [{"kind": "missing", "text": "Not disclosed in the documents provided."}]})
                continue
            best = values[0]
            distinct = sorted({round(v.normalized_value or 0, 6) for v in values})
            if len(distinct) > 1 and distinct[0] and (distinct[-1] - distinct[0]) / abs(distinct[0]) > CONFLICT_TOLERANCE:
                notes.append({"kind": "conflict", "text": f"{len(distinct)} different values appear in this company's "
                                                          "documents; the highest-confidence value is shown."})
            if best.unit and best.normalized_unit and best.unit != best.normalized_unit and \
                    not metric.unit.startswith("tCO2e per"):
                notes.append({"kind": "converted", "text": f"Converted from {best.unit}."})
            if best.method == "text" and any(v.method == "table" for v in values):
                pass
            passage = ctx.passages.get(best.passage_id)
            if passage is not None and passage.extraction_method == "ocr":
                notes.append({"kind": "ocr", "text": f"Read from a scanned page (OCR confidence "
                                                     f"{passage.confidence:.2f})."})
            if best.period_inferred:
                notes.append({"kind": "period", "text": "Period inferred from the document, not stated with the value."})
            if company.id != focal.id and not period_matches(periods[company.id].start, periods[company.id].end,
                                                             focal_period, tolerance=0.98):
                notes.append({"kind": "period", "text": f"Different reporting period ({describe(periods[company.id])})."})
            if metric.key.startswith("ghg_") and company.id != focal.id:
                fb, cb = boundaries.get(focal.id), boundaries.get(company.id)
                if fb and cb and fb["approach"] != cb["approach"]:
                    notes.append({"kind": "boundary", "text": f"Consolidated by {cb['approach']} "
                                                              f"(focal company: {fb['approach']})."})
                elif cb is None:
                    notes.append({"kind": "boundary", "text": "Consolidation approach not stated."})
            if metric.key == "ghg_intensity":
                notes.append({"kind": "denominator", "text": f"Denominator: {best.unit or 'not stated'}."})
            if metric.key == "energy_renewable_share":
                scope = "electricity" if passage is not None and "electric" in passage.text.lower() else "energy"
                notes.append({"kind": "scope", "text": f"Share of {scope}."})
            cell = {"company_id": company.id, "status": "disclosed", **_value_view(best, ctx, session),
                    "alternatives": len(values) - 1, "notes": notes}
            cells.append(cell)

        disclosed = [c for c in cells if c["status"] == "disclosed"]
        units = {c.get("normalized_unit") for c in disclosed}
        comparable = len(disclosed) >= 2 and len(units) == 1 and not any(
            n["kind"] in ("period", "boundary", "method", "conflict", "denominator")
            for c in disclosed for n in c["notes"])
        rows.append({
            "metric_key": metric.key, "label": metric.label, "unit": metric.unit, "question": metric.question,
            "lower_is_better": metric.lower_is_better, "cells": cells, "coverage": f"{len(disclosed)}/{len(cells)}",
            "comparable": comparable,
            "comparability": "Directly comparable" if comparable else (
                "Limited comparability — see notes" if len(disclosed) >= 2 else "Insufficient disclosure to compare"),
        })

    series = _time_series(contexts, companies)
    return {
        "period_label": period_label,
        "companies": [{
            "id": c.id, "name": c.name, "is_focal": c.id == focal.id, "is_sample": c.is_sample,
            "fiscal_year_end": c.fiscal_year_end, "period": {"label": periods[c.id].label,
                                                             "start": periods[c.id].start.isoformat(),
                                                             "end": periods[c.id].end.isoformat(),
                                                             "description": describe(periods[c.id])},
            "boundary": boundaries.get(c.id),
            "documents": len(contexts[c.id].documents),
        } for c in companies],
        "rows": rows,
        "series": series,
    }


def _time_series(contexts: dict[str, AssessmentContext], companies: list[Company]) -> dict:
    out: dict[str, dict[str, list[dict]]] = {}
    for metric in BENCHMARK_METRICS:
        per_company: dict[str, list[dict]] = {}
        for company in companies:
            ctx = contexts[company.id]
            values = [m for m in ctx.metrics_any_period([metric.key]) if not m.is_base_year and m.period_end]
            by_period: dict[str, MetricView] = {}
            for v in sorted(values, key=lambda m: (m.method != "table", -m.confidence)):
                by_period.setdefault(v.period_label or "", v)
            points = sorted(by_period.values(), key=lambda m: m.period_end)
            per_company[company.id] = [{"period_label": p.period_label, "period_end": p.period_end.isoformat(),
                                        "value": p.normalized_value, "unit": p.normalized_unit,
                                        "passage_id": p.passage_id} for p in points]
        out[metric.key] = per_company
    return out


def company_metrics(session: Session, org_id: str, company: Company) -> list[dict]:
    """Every extracted metric for a company's current documents, grouped for the overview page."""
    docs = [d for d in current_documents(session, org_id, company.id) if d.status == "ready"]
    doc_map = {d.id: d for d in docs}
    if not docs:
        return []
    from veridion.models import ExtractedMetric

    rows = session.execute(
        select(ExtractedMetric, Passage.page).join(Passage, Passage.id == ExtractedMetric.passage_id)
        .where(ExtractedMetric.org_id == org_id, ExtractedMetric.document_id.in_(list(doc_map)))
    ).all()
    out = []
    for m, page in rows:
        doc: Document = doc_map[m.document_id]
        out.append({
            "id": m.id, "metric_key": m.metric_key, "label": METRIC_BY_KEY[m.metric_key].label
            if m.metric_key in METRIC_BY_KEY else m.label, "value": m.value, "unit": m.unit,
            "normalized_value": m.normalized_value, "normalized_unit": m.normalized_unit,
            "period_label": m.period_label, "period_end": m.period_end.isoformat() if m.period_end else None,
            "qualifiers": m.qualifiers, "confidence": m.confidence, "method": m.method,
            "passage_id": m.passage_id, "document_id": m.document_id, "document_title": doc.title, "page": page,
            "source": f"{short_doc_name(doc)}, p.{page}",
        })
    out.sort(key=lambda r: (r["metric_key"], r["period_end"] or "", -r["confidence"]))
    return out
