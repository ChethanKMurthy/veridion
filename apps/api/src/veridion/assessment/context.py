"""Everything an assessment needs to know about one company's evidence."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from veridion.extraction.periods import Period
from veridion.models import Document, ExtractedMetric, Passage
from veridion.retrieval import BM25Index, Doc

DOC_TYPE_LABEL = {
    "annual_report": "Annual report",
    "sustainability_report": "Sustainability report",
    "policy": "Policy",
    "data_sheet": "Data sheet",
    "other": "Document",
}


@dataclass
class MetricView:
    id: str
    passage_id: str
    document_id: str
    metric_key: str
    label: str | None
    value: float
    unit: str | None
    normalized_value: float | None
    normalized_unit: str | None
    period_label: str | None
    period_start: date | None
    period_end: date | None
    qualifiers: dict
    confidence: float
    method: str

    @classmethod
    def from_row(cls, m: ExtractedMetric) -> MetricView:
        return cls(m.id, m.passage_id, m.document_id, m.metric_key, m.label, m.value, m.unit, m.normalized_value,
                   m.normalized_unit, m.period_label, m.period_start, m.period_end, dict(m.qualifiers or {}),
                   m.confidence, m.method)

    @property
    def is_base_year(self) -> bool:
        return bool(self.qualifiers.get("base_year"))

    @property
    def period_inferred(self) -> bool:
        return bool(self.qualifiers.get("period_inferred"))


def period_matches(start: date | None, end: date | None, period: Period, tolerance: float = 0.9) -> bool:
    """True when [start, end] covers at least `tolerance` of the period and is not much longer."""
    if start is None or end is None:
        return False
    overlap = (min(end, period.end) - max(start, period.start)).days + 1
    span = (period.end - period.start).days + 1
    length = (end - start).days + 1
    return overlap >= tolerance * span and length <= span / tolerance


@dataclass
class AssessmentContext:
    company_id: str
    period: Period
    documents: dict[str, Document]
    passages: dict[str, Passage]
    ordered_passage_ids: list[str]
    metrics: list[MetricView]
    metric_keys_by_passage: dict[str, set[str]] = field(default_factory=dict)
    index: BM25Index | None = None

    @classmethod
    def load(cls, session: Session, org_id: str, company_id: str, documents: list[Document],
             period: Period) -> AssessmentContext:
        doc_ids = [d.id for d in documents]
        order = {d.id: i for i, d in enumerate(documents)}
        passages = list(session.execute(
            select(Passage).where(Passage.org_id == org_id, Passage.document_id.in_(doc_ids))
        ).scalars()) if doc_ids else []
        passages.sort(key=lambda p: (order[p.document_id], p.page, p.ordinal))
        metrics = [MetricView.from_row(m) for m in session.execute(
            select(ExtractedMetric).where(ExtractedMetric.org_id == org_id, ExtractedMetric.document_id.in_(doc_ids))
        ).scalars()] if doc_ids else []
        keys_by_passage: dict[str, set[str]] = defaultdict(set)
        for m in metrics:
            keys_by_passage[m.passage_id].add(m.metric_key)
        ctx = cls(
            company_id=company_id, period=period, documents={d.id: d for d in documents},
            passages={p.id: p for p in passages}, ordered_passage_ids=[p.id for p in passages],
            metrics=metrics, metric_keys_by_passage=dict(keys_by_passage),
        )
        ctx.index = BM25Index([
            Doc(p.id, p.text, p.section, p.kind, frozenset(keys_by_passage.get(p.id, set()))) for p in passages
        ])
        return ctx

    # --- lookups ------------------------------------------------------------------
    def metrics_for(self, keys: list[str] | set[str], *, period: Period | None = None,
                    include_base_year: bool = False) -> list[MetricView]:
        period = period or self.period
        keys = set(keys)
        out = [
            m for m in self.metrics
            if m.metric_key in keys and (include_base_year or not m.is_base_year)
            and period_matches(m.period_start, m.period_end, period)
        ]
        out.sort(key=lambda m: (m.method != "table", -m.confidence))
        return out

    def metrics_any_period(self, keys: list[str] | set[str]) -> list[MetricView]:
        keys = set(keys)
        return [m for m in self.metrics if m.metric_key in keys]

    def passage_ref(self, passage_id: str) -> str:
        p = self.passages.get(passage_id)
        if p is None:
            return passage_id
        doc = self.documents.get(p.document_id)
        name = short_doc_name(doc) if doc else "Document"
        return f"{name}, p.{p.page}"


def short_doc_name(doc: Document) -> str:
    label = DOC_TYPE_LABEL.get(doc.doc_type, "Document")
    return f"{label} {doc.period_label}" if doc.period_label else label
