"""Units, numbers, periods and metric detection."""

from datetime import date

import pytest

from veridion.extraction.metrics import extract_from_table_row, extract_from_text
from veridion.extraction.numbers import parse_number
from veridion.extraction.periods import find_periods, fiscal_year, parse_period_label
from veridion.extraction.units import find_unit, match_unit_at_start, normalize

CY2025 = fiscal_year(2025, "12-31")


@pytest.mark.parametrize("text,symbol,factor", [
    (" tCO2e", "tCO2e", 1.0),
    (" tonnes of CO2e", "tCO2e", 1.0),
    (" t CO₂e", "tCO2e", 1.0),
    (" ktCO2e", "ktCO2e", 1000.0),
    (" thousand tonnes CO2e", "ktCO2e", 1000.0),
    (" kgCO2e", "kgCO2e", 0.001),
    (" GWh", "GWh", 1000.0),
    (" megalitres", "ML", 1000.0),
])
def test_units_normalise_to_family_base(text, symbol, factor):
    unit, _ = match_unit_at_start(text)
    assert unit.symbol == symbol
    assert normalize(1.0, unit)[0] == pytest.approx(factor)


def test_gigajoules_convert_to_megawatt_hours():
    unit, _ = match_unit_at_start(" GJ")
    value, base = normalize(1_532_000, unit)
    assert base == "MWh"
    assert value == pytest.approx(425_555.56, rel=1e-6)


def test_unit_search_in_table_labels():
    assert find_unit("Scope 1 emissions (tCO2e)").symbol == "tCO2e"
    assert find_unit("Water withdrawal ('000 m3)").symbol == "thousand m3"
    assert find_unit("Waste generated (t)").symbol == "t"
    assert find_unit("Total energy") is None


@pytest.mark.parametrize("raw,expected", [
    ("12,450", 12450.0), ("12 450", 12450.0), ("(310)", -310.0), ("1.2 million", 1_200_000.0),
    ("—", None), ("0.82", 0.82), ("₹1,234 crore", 12_340_000_000.0),
])
def test_parse_number(raw, expected):
    assert parse_number(raw) == expected


def test_periods_respect_fiscal_year_end():
    p = parse_period_label("FY2025", "03-31")
    assert (p.start, p.end) == (date(2024, 4, 1), date(2025, 3, 31))
    p = parse_period_label("2025", "12-31")
    assert (p.start, p.end) == (date(2025, 1, 1), date(2025, 12, 31))
    explicit = find_periods("for the year ended 31 December 2025")[0][0]
    assert explicit.explicit and explicit.end == date(2025, 12, 31)
    us = find_periods("Year ending March 31, 2025", "03-31")[0][0]
    assert us.start == date(2024, 4, 1)
    assert find_periods("FY2024/25 results", "03-31")[0][0].label == "FY2025"


def _keys(text, period=CY2025, fye="12-31"):
    return [(v.metric_key, v.value, v.period_label, v.period_inferred) for v in extract_from_text(text, period, fye)]


def test_scope_values_and_periods():
    assert _keys("In 2025, our gross Scope 1 emissions were 48,210 tCO2e, a 3.8% reduction from 2024.") == [
        ("ghg_scope1", 48210.0, "FY2025", False)]
    assert _keys("Scope 1 emissions were 48,210 tCO2e in 2025, compared with 50,115 tCO2e in 2024.") == [
        ("ghg_scope1", 48210.0, "FY2025", False), ("ghg_scope1", 50115.0, "FY2024", False)]
    # A parenthetical prior-year label belongs to the following value only.
    assert _keys("Scope 1 emissions: 48,210 tCO2e (2024: 50,115 tCO2e).") == [
        ("ghg_scope1", 48210.0, "FY2025", True), ("ghg_scope1", 50115.0, "FY2024", False)]


def test_scope_2_methods_are_distinguished():
    values = extract_from_text("Scope 2 (location-based) emissions totalled 21,940 tonnes of CO2e and market-based "
                               "Scope 2 emissions were 18,300 tCO2e.", CY2025)
    assert [(v.metric_key, v.qualifiers["method"]) for v in values] == [
        ("ghg_scope2_location", "location-based"), ("ghg_scope2_market", "market-based")]


def test_base_year_and_baseline_handling():
    base = extract_from_text("In the 2019 base year, Scope 1 and 2 emissions were 81,600 tCO2e.", CY2025)[0]
    assert base.period_label == "FY2019" and base.qualifiers["base_year"]
    saving = extract_from_text("Efficiency projects delivered energy savings of 6,800 MWh in 2025 against the 2024 "
                               "baseline.", CY2025)[0]
    assert saving.metric_key == "energy_reduction" and saving.period_label == "FY2025"


def test_wrapped_wording_and_targets():
    assert _keys("The Group consumed 1.53 million GJ of energy during the year.")[0][:2] == ("energy_total", 1_530_000.0)
    assert _keys("We target a 30% reduction in Scope 1 and 2 emissions by 2030 against a 2019 base year.") == []


def test_table_rows_use_header_periods_and_skip_fuel_components():
    rows = extract_from_table_row("Scope 1 emissions (tCO2e)", ["48,210", "50,115"], ["2025", "2024"],
                                  default_period=CY2025)
    assert [(r.metric_key, r.value, r.period_label) for r in rows] == [
        ("ghg_scope1", 48210.0, "FY2025"), ("ghg_scope1", 50115.0, "FY2024")]
    assert extract_from_table_row("Natural gas (MWh)", ["268,400"], ["2025"],
                                  table_context="Table 5: Energy consumption (MWh)", default_period=CY2025) == []
    sub = extract_from_table_row("Location-based", ["17,620"], ["FY2024/25"], table_context="Scope 2 emissions (tCO2e)",
                                 default_period=fiscal_year(2025, "03-31"), fiscal_year_end="03-31")
    assert sub[0].metric_key == "ghg_scope2_location"


def test_rates_without_units():
    values = extract_from_text("Our lost-time injury frequency rate (LTIFR) was 0.82 per million hours worked in 2025.",
                               CY2025)
    assert [(v.metric_key, v.value, v.period_label) for v in values] == [("ltifr", 0.82, "FY2025")]
