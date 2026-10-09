"""Deterministic metric extraction from passages and table rows.

Each value is paired with a unit, a reporting period and qualifiers (Scope 2
method, restatement, estimation). A value is only assigned to a metric when
both the unit family and the surrounding wording agree. When the system is
unsure, it extracts nothing rather than guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from veridion.extraction.numbers import NUMBER_RE, looks_like_year, parse_number
from veridion.extraction.periods import Period, find_bare_years, find_periods, parse_period_label
from veridion.extraction.units import Unit, find_unit, match_unit_at_start, normalize


@dataclass(frozen=True)
class MetricDef:
    key: str
    label: str
    family: str
    patterns: tuple[re.Pattern[str], ...]
    exclude: tuple[re.Pattern[str], ...] = ()
    priority: int = 5


def _rx(*patterns: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(p, re.IGNORECASE) for p in patterns)


_S12 = r"scope\s*1\s*(?:and|&|\+|,|/)\s*(?:scope\s*)?2"
_S123 = rf"{_S12}\s*(?:and|&|\+|,|/)\s*(?:scope\s*)?3"
_REDUCTION = r"(?:reduc|avoid|abat|sav|cut)\w*"
_FUEL_COMPONENT = r"\b(?:natural\s+gas|diesel|petrol|gasoline|coal|petcoke|fuel\s+oil|biomass|lpg|propane|kerosene)\b"
_FUEL_COMPONENT_RE = re.compile(_FUEL_COMPONENT, re.IGNORECASE)
_PERIOD_TOKEN = r"(?:FY\s?)?(?:19|20)\d{2}(?:\s?[/–-]\s?\d{2,4})?"
_BASE_YEAR_STATEMENT = re.compile(
    rf"(?:in\s+(?:the|our)\s+)?(?:(?P<label1>{_PERIOD_TOKEN})\s+base[\s-]?year"
    rf"|base[\s-]?year\s+(?:of\s+|was\s+|is\s+)?(?P<label2>{_PERIOD_TOKEN}))",
    re.IGNORECASE,
)
_REDUCTION_KEYS = {"ghg_reduction", "energy_reduction"}

METRICS: tuple[MetricDef, ...] = (
    MetricDef("ghg_biogenic", "Biogenic CO2 emissions", "emissions", _rx(r"biogenic"), priority=9),
    MetricDef("ghg_reduction", "GHG emissions reduced through initiatives", "emissions",
              _rx(rf"{_REDUCTION}[^.]{{0,40}}(?:emissions|ghg|co2)", r"emissions?\s+(?:reductions?|savings?|avoided)"),
              exclude=_rx(r"target"), priority=8),
    MetricDef("ghg_scope2_location", "Scope 2 GHG emissions (location-based)", "emissions",
              _rx(r"scope\s*2\b[^.;]{0,80}location[\s-]based", r"location[\s-]based[^.;]{0,60}scope\s*2"),
              exclude=_rx(_S12), priority=7),
    MetricDef("ghg_scope2_market", "Scope 2 GHG emissions (market-based)", "emissions",
              _rx(r"scope\s*2\b[^.;]{0,80}market[\s-]based", r"market[\s-]based[^.;]{0,60}scope\s*2"),
              exclude=_rx(_S12), priority=7),
    MetricDef("ghg_total", "Total GHG emissions (Scopes 1, 2 and 3)", "emissions",
              _rx(_S123, r"total\s+(?:gross\s+)?(?:ghg|greenhouse\s+gas)\s+emissions"), priority=6),
    MetricDef("ghg_scope1_2", "Scope 1 and 2 GHG emissions", "emissions", _rx(_S12), exclude=_rx(_S123), priority=6),
    MetricDef("ghg_scope1", "Scope 1 GHG emissions", "emissions",
              _rx(r"scope\s*1\b", r"direct\s+(?:\(scope\s*1\)\s+)?(?:ghg\s+|greenhouse\s+gas\s+|co2e?\s+)?emissions"),
              exclude=_rx(_S12), priority=5),
    MetricDef("ghg_scope3", "Scope 3 GHG emissions", "emissions",
              _rx(r"scope\s*3\b", r"other\s+indirect\s+(?:\(scope\s*3\)\s+)?(?:ghg\s+)?emissions",
                  r"value[\s-]chain\s+emissions"),
              exclude=_rx(_S123), priority=5),
    MetricDef("ghg_scope2", "Scope 2 GHG emissions (method not stated)", "emissions",
              _rx(r"scope\s*2\b", r"(?:energy\s+)?indirect\s+\(scope\s*2\)"), exclude=_rx(_S12), priority=4),
    MetricDef("energy_reduction", "Reduction in energy consumption", "energy",
              _rx(rf"{_REDUCTION}[^.]{{0,50}}(?:energy|consumption|mwh|gj)", r"energy\s+(?:savings?|reductions?)"),
              exclude=_rx(r"target"), priority=8),
    MetricDef("energy_electricity", "Electricity consumption", "energy",
              _rx(r"electricity\s+(?:consumption|consumed|purchased|use)", r"purchased\s+electricity",
                  r"consum\w+\s+[^.]{0,20}electricity"), priority=6),
    MetricDef("energy_fuel", "Total fuel consumption", "energy",
              _rx(r"(?:total\s+)?fuel\s+(?:consumption|consumed|use)"), exclude=_rx(_FUEL_COMPONENT), priority=6),
    MetricDef("energy_total", "Total energy consumption", "energy",
              _rx(r"energy\s+(?:consumption|consumed|use)", r"consum\w+\s+(?:a\s+total\s+of\s+)?[^.]{0,30}energy",
                  r"total\s+energy"), priority=4),
    MetricDef("energy_renewable_share", "Share of renewable energy", "percent",
              _rx(r"renewable"), exclude=_rx(r"target|by\s+20\d\d"), priority=5),
    MetricDef("water_withdrawal", "Water withdrawal", "volume",
              _rx(r"water\s+withdraw", r"withdr\w+[^.]{0,40}water", r"water\s+(?:intake|abstraction)"), priority=5),
    MetricDef("water_consumption", "Water consumption", "volume", _rx(r"water\s+consum", r"consum\w+[^.]{0,30}water"),
              priority=4),
    MetricDef("waste_generated", "Waste generated", "mass",
              _rx(r"waste\s+generat", r"generat\w+[^.]{0,40}waste", r"total\s+waste"), priority=5),
    MetricDef("ghg_intensity", "GHG emissions intensity", "intensity_emissions",
              _rx(r"intensity", r"per\s+(?:tonne|unit|€|\$|£|₹|million)"), priority=5),
    MetricDef("energy_intensity", "Energy intensity", "intensity_energy",
              _rx(r"intensity", r"per\s+(?:tonne|unit|€|\$|£|₹|million)"), priority=5),
)

METRIC_BY_KEY = {m.key: m for m in METRICS}

# Rates that are reported without units.
RATE_METRICS = (
    ("ltifr", "Lost-time injury frequency rate",
     re.compile(r"(?:LTIFR|lost[\s-]time\s+injury\s+frequency\s+rate)", re.IGNORECASE)),
    ("trir", "Total recordable injury rate",
     re.compile(r"(?:TRIR|total\s+recordable\s+(?:injury|incident)\s+(?:frequency\s+)?rate)", re.IGNORECASE)),
)

_METHOD_LOCATION = re.compile(r"location[\s-]based", re.IGNORECASE)
_METHOD_MARKET = re.compile(r"market[\s-]based", re.IGNORECASE)
_RESTATED = re.compile(r"restat", re.IGNORECASE)
_ESTIMATED = re.compile(r"\bestimat", re.IGNORECASE)
_COMPARATIVE = re.compile(
    r"(?:from|since|compared\s+(?:with|to)|vs\.?|versus|relative\s+to|against|prior|previous|baseline|base)\s*(?:a|the|year|levels?|in)?\s*$",
    re.IGNORECASE,
)
_LABELS_NEXT_VALUE = re.compile(r"\s*:\s*[-−(]?\d")
_BASE_AFTER = re.compile(r"^\s*(?:base(?:line)?\s+year|baseline|levels?)", re.IGNORECASE)
_INTENSITY_TAIL = re.compile(r"^\s*(?:per|/)\s*(?P<denom>[^.,;:()]{1,40})", re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"(?<=[.;!?])\s+(?=[A-Z(])")


@dataclass
class MetricValue:
    metric_key: str
    label: str
    value: float
    unit: str | None
    normalized_value: float | None
    normalized_unit: str | None
    period: Period | None
    period_inferred: bool
    qualifiers: dict = field(default_factory=dict)
    confidence: float = 0.8
    method: str = "text"
    raw_text: str = ""

    @property
    def period_label(self) -> str | None:
        return self.period.label if self.period else None

    @property
    def period_start(self) -> date | None:
        return self.period.start if self.period else None

    @property
    def period_end(self) -> date | None:
        return self.period.end if self.period else None


def classify(context: str, family: str) -> MetricDef | None:
    best: MetricDef | None = None
    for metric in METRICS:
        if metric.family != family:
            continue
        if not any(p.search(context) for p in metric.patterns):
            continue
        if any(x.search(context) for x in metric.exclude):
            continue
        if best is None or metric.priority > best.priority:
            best = metric
    return best


def qualifiers_for(context: str) -> dict:
    q: dict = {}
    if _METHOD_LOCATION.search(context):
        q["method"] = "location-based"
    if _METHOD_MARKET.search(context):
        q["method"] = "market-based" if "method" not in q else "both mentioned"
    if _RESTATED.search(context):
        q["restated"] = True
    if _ESTIMATED.search(context):
        q["estimated"] = True
    return q


def _pick_period(sentence: str, start: int, end: int, fiscal_year_end: str | None) -> Period | None:
    """Choose the period mention that best describes the value at [start, end)."""
    mentions = find_periods(sentence, fiscal_year_end)
    spans = [(s, e) for _, s, e in mentions]
    for p, s, e in find_bare_years(sentence, fiscal_year_end):
        if all(e <= ts or s >= te for ts, te in spans):
            mentions.append((p, s, e))
    best: tuple[float, Period] | None = None
    for period, s, e in mentions:
        if s < end and e > start:  # overlaps the number itself
            continue
        distance = start - e if e <= start else s - end
        before = sentence[max(0, s - 18):s]
        after = sentence[e:e + 20]
        penalty = 0.0
        if _COMPARATIVE.search(before) or _BASE_AFTER.search(after):
            penalty = 200.0
        elif s >= end and _LABELS_NEXT_VALUE.match(after):
            penalty = 200.0  # "(2024: 50,115 tCO2e)" labels the following value, not this one
        score = distance + penalty
        if best is None or score < best[0]:
            best = (score, period)
    if best is None or best[0] >= 200.0:
        return None  # only comparison or base-year mentions: the period must come from the document
    return best[1]


def _base_year_before(text: str, fye: str | None) -> Period | None:
    """'In the 2019 base year, Scope 1 and 2 emissions were …' → FY2019."""
    hits = list(_BASE_YEAR_STATEMENT.finditer(text))
    if not hits:
        return None
    last = hits[-1]
    label = last.group("label1") or last.group("label2")
    return parse_period_label(label, fye) if label else None


def extract_from_text(text: str, default_period: Period | None, fiscal_year_end: str | None = "12-31",
                      section: str | None = None) -> list[MetricValue]:
    results: list[MetricValue] = []
    sentences = _SENTENCE_SPLIT.split(text)
    for sentence in sentences:
        results.extend(_extract_sentence(sentence, default_period, fiscal_year_end, section))
    results.extend(_extract_rates(text, default_period, fiscal_year_end))
    return results


def _extract_sentence(sentence: str, default_period: Period | None, fye: str | None,
                      section: str | None) -> list[MetricValue]:
    out: list[MetricValue] = []
    prev_end = 0
    prev_metric: MetricDef | None = None
    prev_family: str | None = None
    for m in NUMBER_RE.finditer(sentence):
        raw_num = m.group(0)
        if looks_like_year(m.group("num")) and not m.group("scale"):
            continue
        unit_hit = match_unit_at_start(sentence[m.end():])
        if not unit_hit:
            continue
        unit, unit_len = unit_hit
        tail_start = m.end() + unit_len
        family = unit.family
        unit_symbol = unit.symbol
        intensity = _INTENSITY_TAIL.match(sentence[tail_start:])
        if intensity and family in ("emissions", "energy"):
            family = f"intensity_{family}"
            unit_symbol = f"{unit.symbol}/{intensity.group('denom').strip()}"
        value = parse_number(raw_num)
        if value is None:
            continue

        before = sentence[prev_end:m.start()]
        after = sentence[tail_start:tail_start + 90]
        next_number = NUMBER_RE.search(after)
        after_clause = after[: next_number.start()] if next_number else after
        metric = classify(before, family)
        confidence = 0.85
        if metric is None:
            # Wording that wraps the value: "consumed 1.53 million GJ of energy".
            metric = classify(f"{before} X {after_clause}", family)
            confidence = 0.78
        if metric is None and prev_metric is not None and prev_family == family:
            metric, confidence = prev_metric, 0.7  # "…48,210 tCO2e in 2025, compared with 50,115 tCO2e in 2024"
        if metric is None and section:
            metric = classify(section, family)
            confidence = 0.6
        prev_end = tail_start
        if metric is None:
            continue
        prev_metric, prev_family = metric, family

        period = _pick_period(sentence, m.start(), tail_start, fye)
        inferred = period is None
        base_year = None
        if metric.key not in _REDUCTION_KEYS:
            base_year = _base_year_before(sentence[: m.start()], fye)
        if base_year is not None:
            period, inferred = base_year, False
        elif inferred:
            period = default_period
            confidence -= 0.1
        q = qualifiers_for(sentence)
        if base_year is not None:
            q["base_year"] = True
        if metric.key == "ghg_scope2_location":
            q["method"] = "location-based"
        elif metric.key == "ghg_scope2_market":
            q["method"] = "market-based"
        if family.startswith("intensity"):
            norm_value, norm_unit = value, unit_symbol
        else:
            norm_value, norm_unit = normalize(value, unit)
        out.append(MetricValue(
            metric_key=metric.key, label=metric.label, value=value, unit=unit_symbol,
            normalized_value=norm_value, normalized_unit=norm_unit, period=period, period_inferred=inferred,
            qualifiers=q, confidence=round(confidence, 2), method="text", raw_text=sentence.strip()[:500],
        ))
    return out


_RATE_VALUE = re.compile(r"[^.\d]{0,60}?(?P<num>\d+(?:\.\d+)?)")


def _extract_rates(text: str, default_period: Period | None, fye: str | None) -> list[MetricValue]:
    out = []
    taken: set[tuple[str, int]] = set()
    for key, label, rx in RATE_METRICS:
        for m in rx.finditer(text):
            v = _RATE_VALUE.match(text, m.end())
            if not v or looks_like_year(v.group("num")) or (key, v.start("num")) in taken:
                continue
            taken.add((key, v.start("num")))
            sentence_start = max(text.rfind(".", 0, m.start()) + 1, 0)
            sentence_end = text.find(".", v.end())
            sentence = text[sentence_start: sentence_end if sentence_end != -1 else len(text)]
            local_start = v.start("num") - sentence_start
            period = _pick_period(sentence, local_start, local_start + len(v.group("num")), fye)
            inferred = period is None
            value = float(v.group("num"))
            out.append(MetricValue(
                metric_key=key, label=label, value=value, unit="rate", normalized_value=value,
                normalized_unit="rate", period=period or default_period, period_inferred=inferred,
                qualifiers=qualifiers_for(sentence), confidence=0.75 if not inferred else 0.65,
                method="text", raw_text=sentence.strip()[:500],
            ))
    return out


def extract_from_table_row(label: str, values: list[str], headers: list[str], *, table_context: str = "",
                           default_period: Period | None = None, fiscal_year_end: str | None = "12-31",
                           unit_hint: str | None = None) -> list[MetricValue]:
    """Extract metrics from one table row: a label cell and value cells under period headers."""
    label_clean = " ".join(label.split())
    unit: Unit | None = (
        find_unit(label_clean)
        or (find_unit(unit_hint) if unit_hint else None)
        or (find_unit(table_context) if table_context else None)
    )
    family: str | None = unit.family if unit else None
    rate_key = next(((k, lbl) for k, lbl, rx in RATE_METRICS if rx.search(label_clean)), None)

    metric: MetricDef | None = None
    if family:
        if re.search(r"intensity|\bper\b|/", label_clean, re.IGNORECASE) and family in ("emissions", "energy"):
            family = f"intensity_{family}"
        metric = classify(label_clean, family)
        if metric is None and not _FUEL_COMPONENT_RE.search(label_clean):
            metric = classify(f"{table_context} {label_clean}", family)
    if metric is None and rate_key is None:
        return []

    out: list[MetricValue] = []
    for cell, header in zip(values, headers, strict=False):
        value = parse_number(cell)
        if value is None:
            continue
        cell_unit = unit
        if cell.strip().endswith("%"):
            cell_unit = find_unit("%")
        period = parse_period_label(header, fiscal_year_end) if header else None
        inferred = period is None
        if inferred:
            period = default_period
        context = f"{table_context} {label_clean} {header}"
        q = qualifiers_for(context)
        if rate_key and metric is None:
            out.append(MetricValue(
                metric_key=rate_key[0], label=rate_key[1], value=value, unit="rate", normalized_value=value,
                normalized_unit="rate", period=period, period_inferred=inferred, qualifiers=q,
                confidence=0.9 if not inferred else 0.7, method="table",
                raw_text=f"{label_clean} | {header}: {cell}",
            ))
            continue
        assert metric is not None
        if metric.key == "ghg_scope2_location":
            q["method"] = "location-based"
        elif metric.key == "ghg_scope2_market":
            q["method"] = "market-based"
        if metric.family.startswith("intensity") or cell_unit is None:
            norm_value, norm_unit = value, (cell_unit.symbol if cell_unit else None)
            unit_symbol = cell_unit.symbol if cell_unit else None
            if metric.family.startswith("intensity") and cell_unit is not None:
                denom = re.search(r"(?:per|/)\s*([^)]+)", label_clean, re.IGNORECASE)
                unit_symbol = f"{cell_unit.symbol}/{denom.group(1).strip()}" if denom else cell_unit.symbol
                norm_unit = unit_symbol
        else:
            norm_value, norm_unit = normalize(value, cell_unit)
            unit_symbol = cell_unit.symbol
        out.append(MetricValue(
            metric_key=metric.key, label=metric.label, value=value, unit=unit_symbol,
            normalized_value=norm_value, normalized_unit=norm_unit, period=period, period_inferred=inferred,
            qualifiers=q, confidence=0.92 if not inferred else 0.72, method="table",
            raw_text=f"{label_clean} | {header}: {cell}",
        ))
    return out
