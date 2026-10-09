"""Apply metric extraction to stored passages."""

from __future__ import annotations

from veridion.extraction.metrics import MetricValue, extract_from_table_row, extract_from_text
from veridion.extraction.periods import Period


def extract_for_passage(kind: str, text: str, section: str | None, cells: dict | None, confidence: float,
                        default_period: Period | None, fiscal_year_end: str | None) -> list[MetricValue]:
    if kind in ("paragraph", "list_item"):
        values = extract_from_text(text, default_period, fiscal_year_end, section=section)
    elif kind == "table_row" and cells:
        context = " ".join(filter(None, [cells.get("caption"), section]))
        values = extract_from_table_row(
            cells.get("label", ""), cells.get("values", []), cells.get("headers", []),
            table_context=context, default_period=default_period, fiscal_year_end=fiscal_year_end,
        )
    else:
        return []
    for value in values:
        value.confidence = round(value.confidence * confidence, 3)
        if value.period_inferred:
            value.qualifiers["period_inferred"] = True
    return values
