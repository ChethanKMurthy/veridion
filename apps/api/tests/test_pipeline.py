"""PDF ingestion: passages, tables, provenance, running headers, OCR."""

import pytest

from veridion.pipeline.pdf import PdfError, parse_pdf
from veridion.pipeline.pdf import tesseract_available as ocr_available

from .conftest import SAMPLES


def test_sustainability_report_structure():
    doc = parse_pdf((SAMPLES / "aldermere-sustainability-report-2025.pdf").read_bytes())
    assert doc.page_count == 7
    assert doc.detected_period.label == "FY2025" and doc.detected_period.start.month == 1
    texts = [p.text for p in doc.passages]
    # Running headers and page numbers are removed.
    assert not any(t.startswith("Aldermere Materials Group · Sustainability Report 2025") for t in texts)
    rows = [p for p in doc.passages if p.kind == "table_row"]
    scope1 = next(p for p in rows if p.cells["label"].startswith("Scope 1"))
    assert scope1.cells["headers"] == ["2025", "2024", "2023"]
    assert scope1.cells["values"][0] == "48,210"
    assert scope1.page == 4 and len(scope1.bbox) == 4
    heading = next(p for p in doc.passages if p.kind == "heading" and p.text == "Methodology")
    assert heading.section == "Greenhouse gas emissions › Methodology"
    # Ligatures are normalised so search works ("Efficiency", not "Eﬃciency").
    assert any("Efficiency projects" in t for t in texts)


def test_rejects_non_pdf():
    with pytest.raises(PdfError):
        parse_pdf(b"not a pdf")


@pytest.mark.skipif(not ocr_available(), reason="tesseract not installed")
def test_scanned_page_is_ocred_into_table_rows():
    doc = parse_pdf((SAMPLES / "corvane-sustainability-update-2025.pdf").read_bytes())
    assert doc.ocr_pages == [3]
    rows = [p for p in doc.passages if p.kind == "table_row" and p.method == "ocr"]
    labels = {p.cells["label"]: p.cells["values"] for p in rows}
    assert labels["Scope 1 emissions (ktCO2e)"] == ["63.4", "66.0"]
    assert all(0.5 < p.confidence <= 1.0 for p in rows)


def test_ocr_disabled_reports_skipped_pages():
    doc = parse_pdf((SAMPLES / "corvane-sustainability-update-2025.pdf").read_bytes(), ocr_enabled=False)
    assert doc.ocr_pages == []
    assert any("no text layer" in w for w in doc.warnings)
