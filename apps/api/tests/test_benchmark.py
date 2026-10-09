"""Peer benchmarking compares like with like and says when it cannot."""

from __future__ import annotations

import pytest

from veridion.benchmarking import benchmark
from veridion.pipeline.pdf import tesseract_available

from .conftest import add_sample_company


@pytest.fixture
def peers(session, org):
    focal = add_sample_company(session, org, "aldermere")
    tessaline = add_sample_company(session, org, "tessaline")
    corvane = add_sample_company(session, org, "corvane")
    return focal, tessaline, corvane


def _row(result, key):
    return next(r for r in result["rows"] if r["metric_key"] == key)


def test_units_are_normalised_and_differences_flagged(session, org, peers):
    focal, tessaline, corvane = peers
    result = benchmark(session, org.id, focal, [tessaline, corvane], "FY2025")
    scope1 = _row(result, "ghg_scope1")
    cells = {c["company_id"]: c for c in scope1["cells"]}
    assert cells[corvane.id]["normalized_value"] == pytest.approx(63_400)
    assert any(n["kind"] == "converted" for n in cells[corvane.id]["notes"])
    assert any(n["kind"] == "period" for n in cells[tessaline.id]["notes"])  # April–March year
    assert any(n["kind"] == "boundary" for n in cells[tessaline.id]["notes"])  # financial vs operational control
    assert scope1["comparable"] is False

    energy = {c["company_id"]: c for c in _row(result, "energy_total")["cells"]}
    assert energy[tessaline.id]["normalized_value"] == pytest.approx(1_298_000 / 3.6)
    assert any(n["kind"] == "conflict" for n in energy[focal.id]["notes"])  # AR vs SR disagreement


def test_missing_values_are_not_zero(session, org, peers):
    focal, tessaline, corvane = peers
    result = benchmark(session, org.id, focal, [tessaline, corvane], "FY2025")
    scope3 = {c["company_id"]: c for c in _row(result, "ghg_scope3")["cells"]}
    assert scope3[focal.id]["status"] == "not_disclosed" and scope3[focal.id]["value"] is None
    assert scope3[tessaline.id]["value"] == 186_300
    method = {c["company_id"]: c for c in _row(result, "ghg_scope2_location")["cells"]}
    assert any(n["kind"] == "method" for n in method[corvane.id]["notes"])


@pytest.mark.skipif(not tesseract_available(), reason="tesseract not installed")
def test_series_includes_prior_periods(session, org, peers):
    focal, tessaline, corvane = peers
    result = benchmark(session, org.id, focal, [tessaline, corvane], "FY2025")
    focal_series = result["series"]["ghg_scope1"][focal.id]
    assert [p["period_label"] for p in focal_series] == ["FY2023", "FY2024", "FY2025"]
