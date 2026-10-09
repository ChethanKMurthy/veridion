"""Catalogue versioning, rules assessment, runs, diffs, actions and evidence lineage."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from sqlalchemy import select

from veridion.assessment.context import AssessmentContext
from veridion.assessment.diff import diff_runs
from veridion.assessment.engine import create_run, stale_findings
from veridion.assessment.rules import assess_requirement
from veridion.catalog import load_catalog, parse_file
from veridion.config import get_settings
from veridion.extraction.periods import fiscal_year
from veridion.jobs import run_pending
from veridion.models import Action, AssessmentRun, Finding, FindingEvidence, Passage, RequirementSet
from veridion.services.documents import create_document, current_documents

from .conftest import SAMPLES, add_sample_company

EXPECTED_V100 = {
    "305-1": "supported", "305-2": "supported", "305-3": "partially_supported", "305-4": "supported",
    "305-5": "supported", "302-1": "conflicting", "302-3": "supported", "302-4": "supported",
    "2-5": "partially_supported",
}


def _assess(session, org, company, set_id):
    rs = session.get(RequirementSet, set_id)
    docs = current_documents(session, org.id, company.id)
    ctx = AssessmentContext.load(session, org.id, company.id, docs, fiscal_year(2025, company.fiscal_year_end))
    return {r.code: assess_requirement(r, ctx) for r in rs.requirements}


def test_catalogue_files_are_valid_and_versioned():
    root = get_settings().catalog_dir
    v1 = parse_file(root / "gri-302-305-2016" / "1.0.0.yaml")
    v11 = parse_file(root / "gri-302-305-2016" / "1.1.0.yaml")
    assert v1.review_status == "reviewed" and v11.changelog[0].version == "1.1.0"
    keys_v1 = {e.key for r in v1.requirements if r.code == "305-1" for e in r.elements}
    keys_v11 = {e.key for r in v11.requirements if r.code == "305-1" for e in r.elements}
    assert keys_v11 - keys_v1 == {"biogenic"}
    draft = parse_file(root / "gri-102-103-2025" / "0.1.0.yaml")
    assert draft.review_status == "draft" and str(draft.effective_from) == "2027-01-01"


def test_catalogue_rejects_invalid_regex(tmp_path: Path):
    src = get_settings().catalog_dir / "gri-302-305-2016" / "1.0.0.yaml"
    data = yaml.safe_load(src.read_text())
    data.pop("shared", None)
    data["requirements"][0]["elements"][2]["check"] = {"type": "pattern", "patterns": ["(unclosed"]}
    target = tmp_path / "gri-302-305-2016" / "1.0.0.yaml"
    target.parent.mkdir()
    target.write_text(yaml.safe_dump(data))
    with pytest.raises(ValueError, match="Invalid regular expression"):
        parse_file(target)


def test_loaded_catalogue_is_immutable_once_used(session, org, tmp_path: Path):
    company = add_sample_company(session, org, "aldermere")
    create_run(session, org_id=org.id, company=company, requirement_set_id="gri-302-305-2016@1.0.0", mode="rules",
               period_label="FY2025", deadline=None, user_id=None)
    session.commit()
    src = get_settings().catalog_dir / "gri-302-305-2016" / "1.0.0.yaml"
    target = tmp_path / "cat" / "gri-302-305-2016" / "1.0.0.yaml"
    target.parent.mkdir(parents=True)
    target.write_text(src.read_text().replace("Initial curated subset", "Edited after use"))
    with pytest.raises(RuntimeError, match="new version"):
        load_catalog(session, tmp_path / "cat")


def test_rules_statuses_for_the_focal_company(session, org):
    company = add_sample_company(session, org, "aldermere")
    results = _assess(session, org, company, "gri-302-305-2016@1.0.0")
    assert {code: r.status for code, r in results.items()} == EXPECTED_V100

    conflict = results["302-1"].conflicts[0]
    assert conflict.metric_key == "energy_total"
    assert conflict.low.normalized_value == pytest.approx(412_300)
    assert conflict.high.normalized_value == pytest.approx(425_555.6, rel=1e-4)
    # Absence of evidence is described, never equated with non-compliance.
    assert "Missing:" in results["305-3"].rationale


def test_catalogue_revision_changes_two_findings(session, org):
    company = add_sample_company(session, org, "aldermere")
    v11 = _assess(session, org, company, "gri-302-305-2016@1.1.0")
    assert v11["305-1"].status == "partially_supported"
    assert [e.key for e in v11["305-1"].elements if e.status == "missing"] == ["biogenic"]
    market = next(e for e in v11["305-2"].elements if e.key == "market_value")
    assert market.status == "missing" and "Guarantees of Origin" in market.note


def test_conditional_element_not_applicable_without_trigger(session, org):
    company = add_sample_company(session, org, "corvane")
    v11 = _assess(session, org, company, "gri-302-305-2016@1.1.0")
    market = next(e for e in v11["305-2"].elements if e.key == "market_value")
    assert market.status == "not_applicable"
    location = next(e for e in v11["305-2"].elements if e.key == "location_value")
    assert location.status == "satisfied" and location.weak  # Scope 2 method not stated


def test_peer_without_disclosures_is_not_found_not_non_compliant(session, org):
    company = add_sample_company(session, org, "corvane")
    v11 = _assess(session, org, company, "gri-302-305-2016@1.1.0")
    assert v11["305-3"].status == "not_found"
    assert "does not establish non-compliance" in v11["305-3"].rationale


def _run(session, org, company, set_id, mode="rules"):
    run, _ = create_run(session, org_id=org.id, company=company, requirement_set_id=set_id, mode=mode,
                        period_label="FY2025", deadline=None, user_id=None)
    session.commit()
    run_pending()
    session.expire_all()
    return session.get(AssessmentRun, run.id)


def test_run_records_manifest_actions_and_diff(session, org):
    company = add_sample_company(session, org, "aldermere")
    first = _run(session, org, company, "gri-302-305-2016@1.0.0")
    assert first.status == "completed", first.error
    assert first.summary["counts"]["conflicting"] == 1
    assert {d["sha256"] for d in first.input_manifest["documents"]}
    assert first.rules_version and first.pipeline_version

    second = _run(session, org, company, "gri-302-305-2016@1.1.0")
    assert second.previous_run_id == first.id
    diff = diff_runs(session, first, second)
    changed = {i["requirement_code"]: i for i in diff["items"] if i["status_changed"]}
    assert set(changed) == {"305-1", "305-2"}
    assert changed["305-1"]["causes"] == ["requirement revised"]

    actions = session.execute(select(Action).where(Action.company_id == company.id)).scalars().all()
    gap_keys = {(a.requirement_code, a.gap_key) for a in actions}
    assert ("302-1", "conflict:energy_total") in gap_keys
    assert ("305-1", "biogenic") in gap_keys
    period = next(a for a in actions if (a.requirement_code, a.gap_key) == ("305-3", "period"))
    value = next(a for a in actions if (a.requirement_code, a.gap_key) == ("305-3", "value"))
    assert period.depends_on == [value.id]
    # Re-running does not duplicate actions.
    _run(session, org, company, "gri-302-305-2016@1.1.0")
    assert len(session.execute(select(Action).where(Action.company_id == company.id)).scalars().all()) == len(actions)


def test_replacing_a_document_marks_findings_stale_and_closes_the_gap(session, org):
    company = add_sample_company(session, org, "aldermere")
    first = _run(session, org, company, "gri-302-305-2016@1.1.0")
    annual = next(d for d in current_documents(session, org.id, company.id) if d.doc_type == "annual_report")
    create_document(session, org_id=org.id, company=company,
                    data=(SAMPLES / "aldermere-annual-report-2025-v2.pdf").read_bytes(),
                    filename="aldermere-annual-report-2025-v2.pdf", title=None, doc_type="annual_report",
                    period_label="FY2025", published_on=None, uploaded_by=None, lineage_id=annual.lineage_id)
    session.commit()
    run_pending()
    session.expire_all()

    stale = stale_findings(session, session.get(AssessmentRun, first.id))
    assert any(s["requirement_code"] == "302-1" for s in stale)

    second = _run(session, org, company, "gri-302-305-2016@1.1.0")
    f = session.execute(select(Finding).where(Finding.run_id == second.id, Finding.requirement_code == "302-1")).scalar_one()
    assert f.status == "supported"  # the corrected annual report agrees with the sustainability report
    conflict_action = session.execute(select(Action).where(Action.company_id == company.id,
                                                           Action.gap_key == "conflict:energy_total")).scalar_one()
    assert conflict_action.gap_closed_run_id == second.id
    diff = diff_runs(session, first, second)
    item = next(i for i in diff["items"] if i["requirement_code"] == "302-1")
    assert "documents changed" in item["causes"]
    assert diff["document_changes"][0]["change"] == "replaced"


def test_not_applicable_requirements_are_excluded_with_rationale(session, org):
    from veridion.models import ApplicabilityDecision

    company = add_sample_company(session, org, "aldermere")
    session.add(ApplicabilityDecision(org_id=org.id, company_id=company.id, set_key="gri-302-305-2016",
                                      requirement_code="302-4", applicable=False,
                                      rationale="No energy conservation programme reported in scope."))
    session.commit()
    run = _run(session, org, company, "gri-302-305-2016@1.1.0")
    assert [e["code"] for e in run.excluded_requirements] == ["302-4"]
    codes = set(session.execute(select(Finding.requirement_code).where(Finding.run_id == run.id)).scalars())
    assert "302-4" not in codes


def test_evidence_links_point_to_real_passages(session, org):
    company = add_sample_company(session, org, "aldermere")
    run = _run(session, org, company, "gri-302-305-2016@1.0.0")
    links = session.execute(select(FindingEvidence).join(Finding).where(Finding.run_id == run.id)).scalars().all()
    assert links
    passage_ids = {p for (p,) in session.execute(select(Passage.id)).all()}
    assert all(link.passage_id in passage_ids for link in links)
    roles = {link.role for link in links}
    assert {"supporting", "conflicting"} <= roles
