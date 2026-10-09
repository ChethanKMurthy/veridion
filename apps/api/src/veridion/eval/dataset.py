"""Evaluation dataset: gold-labelled cases.

Two sources:

1. Corpus cases — the fictional sample companies, labelled by hand from the
   document content (not from system output).
2. Synthetic cases — short generated reports with controlled variation. Each
   element is present in standard wording, present in paraphrase (wording
   that keyword rules are expected to miss), absent, or replaced by a trap
   (wording that looks relevant but does not satisfy the element).

Gold statuses follow the catalogue's element weights: supported when every
applicable element is established, not_found when none is, otherwise
partially_supported; conflicting when two sources disagree by more than 1%.

Limitations: the dataset is authored by the developers and is small. It shows
how the pipeline behaves on controlled cases; it does not establish accuracy
on real-world reports. Add human-reviewed real cases before relying on it.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

SET_ID = "gri-302-305-2016@1.1.0"


@dataclass
class CaseDocument:
    slug: str | None = None  # an existing sample PDF
    pages: list[str] | None = None  # or generated HTML pages
    doc_type: str = "sustainability_report"
    title: str = "Sustainability Report 2025"


@dataclass
class GoldValue:
    metric_key: str
    value: float  # in the family base unit (tCO2e, MWh, …)
    period_label: str


@dataclass
class Case:
    id: str
    source: str  # corpus | synthetic
    requirement_code: str
    fiscal_year_end: str
    documents: list[CaseDocument]
    status: str
    elements: dict[str, bool] = field(default_factory=dict)  # gold element satisfaction (synthetic)
    evidence_pages: list[tuple[int, int]] = field(default_factory=list)  # (document index, page)
    values: list[GoldValue] = field(default_factory=list)
    conflict: bool = False
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Corpus cases (hand-labelled)
# ---------------------------------------------------------------------------

_ALDERMERE = [CaseDocument(slug="aldermere-sustainability-report-2025"),
              CaseDocument(slug="aldermere-annual-report-2025", doc_type="annual_report",
                           title="Annual Report 2025")]
_TESSALINE = [CaseDocument(slug="tessaline-annual-sustainability-report-2024-25")]
_CORVANE = [CaseDocument(slug="corvane-sustainability-update-2025")]

_CORPUS = {
    # company: (documents, fiscal year end, {code: (status, evidence pages, tags)})
    "aldermere": (_ALDERMERE, "12-31", {
        "305-1": ("partially_supported", [(0, 4), (0, 2)], ["biogenic missing"]),
        "305-2": ("partially_supported", [(0, 4)], ["market-based missing", "conditional element"]),
        "305-3": ("partially_supported", [(0, 5)], ["screened not quantified"]),
        "305-4": ("supported", [(0, 4)], []),
        "305-5": ("supported", [(0, 7)], []),
        "302-1": ("conflicting", [(0, 6), (1, 5)], ["cross-document conflict", "unit conversion"]),
        "302-3": ("supported", [(0, 6)], []),
        "302-4": ("supported", [(0, 7)], []),
        "2-5": ("partially_supported", [(0, 2)], ["not assured"]),
    }),
    "tessaline": (_TESSALINE, "03-31", {
        "305-1": ("supported", [(0, 3), (0, 2)], ["fiscal year April–March"]),
        "305-2": ("supported", [(0, 3)], ["market-based present"]),
        "305-3": ("supported", [(0, 3)], []),
        "305-4": ("supported", [(0, 3)], []),
        "305-5": ("partially_supported", [(0, 4)], ["reductions not quantified"]),
        "302-1": ("partially_supported", [(0, 4)], ["conversion factors missing"]),
        "302-3": ("not_found", [], []),
        "302-4": ("not_found", [], ["target baseline is not an energy-savings baseline"]),
        "2-5": ("supported", [(0, 2)], []),
    }),
    "corvane": (_CORVANE, "12-31", {
        "305-1": ("partially_supported", [(0, 2)], ["ktCO2e"]),
        "305-2": ("partially_supported", [(0, 2)], ["method not stated"]),
        "305-3": ("not_found", [], []),
        "305-4": ("not_found", [], []),
        "305-5": ("not_found", [], []),
        "302-1": ("partially_supported", [(0, 2)], ["GWh", "OCR appendix"]),
        "302-3": ("not_found", [], []),
        "302-4": ("not_found", [], []),
        "2-5": ("not_found", [], []),
    }),
}

_CORPUS_VALUES = {
    "aldermere": [GoldValue("ghg_scope1", 48_210, "FY2025"), GoldValue("ghg_scope2_location", 21_940, "FY2025"),
                  GoldValue("ghg_scope1", 50_115, "FY2024"), GoldValue("energy_total", 412_300, "FY2025"),
                  GoldValue("ghg_reduction", 2_350, "FY2025"), GoldValue("energy_reduction", 6_800, "FY2025"),
                  GoldValue("water_withdrawal", 412_000, "FY2025"), GoldValue("ltifr", 0.82, "FY2025")],
    "tessaline": [GoldValue("ghg_scope1", 41_870, "FY2025"), GoldValue("ghg_scope2_market", 9_410, "FY2025"),
                  GoldValue("ghg_scope3", 186_300, "FY2025"), GoldValue("ghg_biogenic", 1_240, "FY2025"),
                  GoldValue("energy_total", 1_298_000 / 3.6, "FY2025"), GoldValue("water_withdrawal", 365_000, "FY2025")],
    "corvane": [GoldValue("ghg_scope1", 63_400, "FY2025"), GoldValue("ghg_scope2", 26_100, "FY2025"),
                GoldValue("energy_total", 498_000, "FY2025"), GoldValue("water_withdrawal", 538_000, "FY2025")],
}


def corpus_cases() -> list[Case]:
    cases = []
    for company, (docs, fye, labels) in _CORPUS.items():
        for code, (status, pages, tags) in labels.items():
            cases.append(Case(
                id=f"corpus/{company}/{code}", source="corpus", requirement_code=code, fiscal_year_end=fye,
                documents=docs, status=status, evidence_pages=pages, conflict=status == "conflicting",
                values=_CORPUS_VALUES[company] if code == "305-1" else [], tags=[company, *tags],
            ))
    return cases


# ---------------------------------------------------------------------------
# Synthetic cases
# ---------------------------------------------------------------------------

COVER = """<h1>Sustainability Report {year}</h1>
<p>This report covers Example Company Ltd for the year ended 31 December {year}. The company and figures are
fictional and were generated for evaluation.</p>"""

# Phrasings per element: (standard wording, paraphrase rules may miss, trap that must NOT count).
PHRASES = {
    "305-1": {
        "value": (["Gross Scope 1 emissions were {v:,} tCO2e in {y}.",
                   "Direct (Scope 1) GHG emissions totalled {v:,} tonnes of CO2e during {y}.",
                   "In {y} our Scope 1 emissions amounted to {kt} ktCO2e."],
                  ["Combustion of fuels at our own sites released {v:,} tCO2e of direct emissions in {y}."],
                  ["We plan to start disclosing Scope 1 emissions next year.",
                   "In {py}, Scope 1 emissions were {v:,} tCO2e."]),
        "boundary": (["Emissions are consolidated using the operational control approach.",
                      "We apply the financial control approach to our greenhouse gas inventory."],
                     ["Our inventory covers every facility we operate and where we can introduce operating policies."],
                     ["Internal control: the Board reviews financial controls over reporting each year."]),
        "methodology": (["Emissions are calculated in line with the GHG Protocol Corporate Standard.",
                         "Our greenhouse gas inventory is prepared in accordance with ISO 14064-1."],
                        ["Calculations follow the WRI/WBCSD corporate accounting framework for greenhouse gases."],
                        ["We have not yet adopted a formal GHG methodology for our emissions."]),
        "gases": (["The inventory covers CO2, CH4 and N2O.",
                   "Carbon dioxide, methane and nitrous oxide are included in the inventory."],
                  ["All six gases listed in the Kyoto Protocol are within the scope of our calculations."],
                  ["Our calculations include the greenhouse gases relevant to our operations."]),
        "factors": (["Emission factors are sourced from DEFRA, and global warming potentials from IPCC AR6.",
                     "We use emission factors published by the IEA."],
                    ["Activity data is converted using the government's published carbon conversion values."],
                    ["Factors affecting our performance include weather and production volumes."]),
        "base_year": (["Our base year for emissions is 2019.",
                       "Base-year emissions were 61,200 tCO2e in 2019 and are recalculated for structural changes."],
                      ["We measure our emissions progress from a 2019 starting point."],
                      ["The year was a challenging one for emissions-intensive industries."]),
        "biogenic": (["Biogenic CO2 emissions from biomass were 1,050 tCO2e and are reported separately.",
                      "No biogenic CO2 emissions arise from our operations."],
                     ["CO2 released from burning wood pellets, 1,050 tonnes, is reported outside the scopes."],
                     []),
    },
    "305-2": {
        "location_value": (["Location-based Scope 2 emissions were {v:,} tCO2e in {y}.",
                            "Scope 2 emissions (location-based) totalled {v:,} tonnes of CO2e in {y}."],
                           [],
                           ["Scope 2 emissions will be reported once electricity data is complete."]),
        "boundary": (["We report GHG emissions using the operational control approach."],
                     [], ["The Audit Committee reviews financial controls."]),
        "methodology": (["Scope 2 is calculated following the GHG Protocol Scope 2 Guidance and Corporate Standard."],
                        [], ["We have not yet formalised our GHG methodology."]),
        "factors": (["Grid emission factors are taken from the IEA.", "We apply DEFRA grid emission factors."],
                    ["Electricity is converted using the national grid operator's published carbon intensity."],
                    []),
        "trigger": (["Two sites purchase electricity under a renewable power purchase agreement (PPA).",
                     "Part of our electricity is backed by guarantees of origin."], [], []),
        "market_value": (["Market-based Scope 2 emissions were {m:,} tCO2e in {y}."], [], []),
    },
    "302-1": {
        "total": (["Total energy consumption within the organization was {e:,} MWh in {y}.",
                   "In {y} we consumed a total of {gj:,} GJ of energy."],
                  ["Our operations used {e:,} MWh of energy across all sites in {y}."],
                  ["Energy consumption is monitored monthly at each site."]),
        "fuel": (["Fuel consumption comprised natural gas and diesel.",
                  "Natural gas accounted for most of our fuel use."],
                 [], ["Fuel prices rose sharply during the year."]),
        "electricity": (["Electricity consumption was {el:,} MWh in {y}.", "Purchased electricity was {el:,} MWh."],
                        [], []),
        "conversion_factors": (["Fuel use is converted to energy using net calorific values.",
                                "Conversion factors are taken from DESNZ."],
                               ["Fuel quantities are translated into energy using the government's published values."],
                               []),
    },
    "2-5": {
        "statement": (["Our GHG data received limited assurance from an independent provider.",
                       "This report has not been externally assured."],
                      ["An independent firm checked our emissions figures and issued a limited-level opinion."],
                      ["We value transparency and robust data."]),
        "scope": (["Limited assurance covered Scope 1 and Scope 2 emissions."], [], []),
        "standard": (["The engagement was performed under ISAE 3410."], [], []),
    },
}

WEIGHTS = {
    "305-1": {"value": 3, "period": 2, "boundary": 2, "methodology": 1, "gases": 1, "factors": 1, "base_year": 1,
              "biogenic": 1},
    "305-2": {"location_value": 3, "period": 2, "boundary": 1, "methodology": 1, "factors": 1, "market_value": 2},
    "302-1": {"total": 3, "fuel": 2, "electricity": 1, "period": 1, "conversion_factors": 1},
    "2-5": {"statement": 2, "scope": 1, "standard": 1},
}


def _gold_status(code: str, elements: dict[str, bool | None]) -> str:
    applicable = {k: v for k, v in elements.items() if v is not None}
    total = sum(WEIGHTS[code][k] for k in applicable)
    got = sum(WEIGHTS[code][k] for k, v in applicable.items() if v)
    if got == total:
        return "supported"
    return "partially_supported" if got > 0 else "not_found"


def _choose(rng: random.Random, options: tuple[list[str], list[str], list[str]], weights=(0.5, 0.17, 0.2, 0.13)):
    standard, paraphrase, trap = options
    kinds = ["standard", "paraphrase", "absent", "trap"]
    available = [k for k in kinds if k == "absent" or (k == "standard" and standard) or
                 (k == "paraphrase" and paraphrase) or (k == "trap" and trap)]
    w = [weights[kinds.index(k)] for k in available]
    kind = rng.choices(available, weights=w)[0]
    if kind == "standard":
        return kind, rng.choice(standard)
    if kind == "paraphrase":
        return kind, rng.choice(paraphrase)
    if kind == "trap":
        return kind, rng.choice(trap)
    return kind, None


def _render(year: int, sentences: list[str], table: str = "") -> list[str]:
    body = "".join(f"<p>{s}</p>" for s in sentences)
    return [COVER.format(year=year) + "<h2>Climate and energy</h2>" + body + table]


def synthetic_cases(seed: int = 7, n_per_requirement: dict[str, int] | None = None) -> list[Case]:
    rng = random.Random(seed)
    counts = n_per_requirement or {"305-1": 40, "305-2": 30, "302-1": 30, "2-5": 12}
    cases: list[Case] = []
    year = 2025

    for i in range(counts["305-1"]):
        v = rng.randrange(8_000, 90_000)
        fmt = {"v": v, "kt": f"{v / 1000:.1f}", "y": year, "py": year - 1}
        sentences, elements, tags, values = [], {}, [], []
        for key in ("value", "boundary", "methodology", "gases", "factors", "base_year", "biogenic"):
            kind, text = _choose(rng, PHRASES["305-1"][key])
            if key == "value" and rng.random() < 0.2 and kind == "standard":
                # Value only in a table.
                kind, text = "table", None
            if text:
                sentences.append(text.format(**fmt))
            elements[key] = kind in ("standard", "paraphrase", "table")
            tags.append(f"{key}:{kind}")
            if key == "value" and elements[key]:
                kt_rounded = "kt" in (text or "")
                values.append(GoldValue("ghg_scope1", float(f"{v / 1000:.1f}") * 1000 if kt_rounded else v, f"FY{year}"))
        table = ""
        if "value:table" in tags:
            table = (f"<table><tr><th>Indicator</th><th>{year}</th><th>{year - 1}</th></tr>"
                     f"<tr><td>Scope 1 emissions (tCO2e)</td><td>{v:,}</td><td>{int(v * 1.04):,}</td></tr></table>")
        elements["period"] = elements["value"]
        rng.shuffle(sentences)
        cases.append(Case(
            id=f"synthetic/305-1/{i:03d}", source="synthetic", requirement_code="305-1", fiscal_year_end="12-31",
            documents=[CaseDocument(pages=_render(year, sentences, table))], status=_gold_status("305-1", elements),
            elements=elements, evidence_pages=[(0, 1)] if any(elements.values()) else [], values=values, tags=tags,
        ))

    for i in range(counts["305-2"]):
        v, m = rng.randrange(5_000, 40_000), rng.randrange(1_000, 5_000)
        fmt = {"v": v, "m": m, "y": year}
        sentences, elements, tags = [], {}, []
        for key in ("location_value", "boundary", "methodology", "factors"):
            kind, text = _choose(rng, PHRASES["305-2"][key])
            if text:
                sentences.append(text.format(**fmt))
            elements[key] = kind in ("standard", "paraphrase")
            tags.append(f"{key}:{kind}")
        elements["period"] = elements["location_value"]
        if rng.random() < 0.5:
            sentences.append(rng.choice(PHRASES["305-2"]["trigger"][0]))
            tags.append("trigger:present")
            has_market = rng.random() < 0.5
            if has_market:
                sentences.append(PHRASES["305-2"]["market_value"][0][0].format(**fmt))
            elements["market_value"] = has_market
            tags.append(f"market_value:{'standard' if has_market else 'absent'}")
        else:
            elements["market_value"] = None  # not applicable
            tags.append("trigger:absent")
        rng.shuffle(sentences)
        cases.append(Case(
            id=f"synthetic/305-2/{i:03d}", source="synthetic", requirement_code="305-2", fiscal_year_end="12-31",
            documents=[CaseDocument(pages=_render(year, sentences))], status=_gold_status("305-2", elements),
            elements={k: bool(v) for k, v in elements.items() if v is not None},
            evidence_pages=[(0, 1)] if any(v for v in elements.values() if v) else [],
            values=[GoldValue("ghg_scope2_location", v, f"FY{year}")] if elements["location_value"] else [], tags=tags,
        ))

    for i in range(counts["302-1"]):
        e = rng.randrange(40_000, 600_000)
        el = rng.randrange(5_000, e // 2)
        conflict_mode = rng.choices(["none", "conflict", "rounding"], weights=[0.6, 0.25, 0.15])[0]
        fmt = {"e": e, "gj": round(e * 3.6), "el": el, "y": year}
        sentences, elements, tags = [], {}, [f"conflict:{conflict_mode}"]
        kind, text = _choose(rng, PHRASES["302-1"]["total"])
        if conflict_mode != "none":
            kind, text = "standard", PHRASES["302-1"]["total"][0][0]
        if text:
            sentences.append(text.format(**fmt))
        elements["total"] = kind in ("standard", "paraphrase")
        tags.append(f"total:{kind}")
        for key in ("fuel", "electricity", "conversion_factors"):
            k2, t2 = _choose(rng, PHRASES["302-1"][key])
            if t2:
                sentences.append(t2.format(**fmt))
            elements[key] = k2 in ("standard", "paraphrase")
            tags.append(f"{key}:{k2}")
        elements["period"] = elements["total"]
        if conflict_mode == "conflict":
            other = round(e * rng.choice([1.03, 0.96, 1.05]) * 3.6)
            sentences.append(f"The annual report states total energy consumption of {other:,} GJ for {year}.")
        elif conflict_mode == "rounding":
            sentences.append(f"Total energy use was approximately {round(e * 3.6, -3):,.0f} GJ in {year}.")
        rng.shuffle(sentences)
        status = "conflicting" if conflict_mode == "conflict" else _gold_status("302-1", elements)
        cases.append(Case(
            id=f"synthetic/302-1/{i:03d}", source="synthetic", requirement_code="302-1", fiscal_year_end="12-31",
            documents=[CaseDocument(pages=_render(year, sentences))], status=status, elements=elements,
            evidence_pages=[(0, 1)] if any(elements.values()) else [], conflict=conflict_mode == "conflict",
            values=[GoldValue("energy_total", e, f"FY{year}")] if elements["total"] else [], tags=tags,
        ))

    for i in range(counts["2-5"]):
        sentences, elements, tags = [], {}, []
        texts: dict[str, str | None] = {}
        for key in ("statement", "scope", "standard"):
            kind, text = _choose(rng, PHRASES["2-5"][key], weights=(0.55, 0.15, 0.2, 0.1))
            if text:
                sentences.append(text)
            texts[key] = text if kind in ("standard", "paraphrase") else None
            tags.append(f"{key}:{kind}")
        # A sentence about the scope or standard of an assurance engagement also states the assurance
        # position, and a statement that names the assured data ("our GHG data received…") states its scope.
        elements["statement"] = any(texts.values())
        elements["scope"] = bool(texts["scope"]) or bool(texts["statement"] and "GHG" in texts["statement"]) \
            or bool(texts["statement"] and "emissions figures" in texts["statement"])
        elements["standard"] = bool(texts["standard"])
        cases.append(Case(
            id=f"synthetic/2-5/{i:03d}", source="synthetic", requirement_code="2-5", fiscal_year_end="12-31",
            documents=[CaseDocument(pages=_render(year, sentences))], status=_gold_status("2-5", elements),
            elements=elements, evidence_pages=[(0, 1)] if any(elements.values()) else [], tags=tags,
        ))
    return cases


def all_cases(seed: int = 7) -> list[Case]:
    return corpus_cases() + synthetic_cases(seed)
