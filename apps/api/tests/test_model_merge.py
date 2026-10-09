"""The model is a reviewer, not an authority: citation validation and merge policy."""

from __future__ import annotations

from sqlalchemy import select

from veridion.assessment.context import AssessmentContext
from veridion.assessment.engine import create_run
from veridion.assessment.llm import assess_with_model
from veridion.assessment.merge import merge
from veridion.assessment.rules import assess_requirement
from veridion.extraction.periods import fiscal_year
from veridion.jobs import run_pending
from veridion.llm import LLMResponse, set_provider
from veridion.models import AssessmentRun, Finding, RequirementSet
from veridion.services.documents import current_documents

from .conftest import add_sample_company


class FakeProvider:
    """Returns scripted judgements; records prompts for inspection."""

    name, model = "fake", "fake-model"

    def __init__(self, script):
        self.script = script
        self.prompts: list[str] = []

    def complete_json(self, system, user, schema, **_):
        self.prompts.append(user)
        return LLMResponse(data=self.script(user), raw="{}", model=self.model,
                           usage={"prompt_tokens": 100, "completion_tokens": 50})


def _context(session, org, company):
    docs = current_documents(session, org.id, company.id)
    return AssessmentContext.load(session, org.id, company.id, docs, fiscal_year(2025, company.fiscal_year_end))


def _requirement(session, set_id, code):
    rs = session.get(RequirementSet, set_id)
    return next(r for r in rs.requirements if r.code == code)


def test_invalid_citations_are_discarded(session, org):
    company = add_sample_company(session, org, "aldermere")
    ctx = _context(session, org, company)
    req = _requirement(session, "gri-302-305-2016@1.1.0", "305-3")
    rules = assess_requirement(req, ctx)
    provider = FakeProvider(lambda _: {
        "status": "supported", "evidence_ids": ["ev_doesnotexist"], "rationale": "Invented.",
        "element_judgements": [{"key": "value", "verdict": "yes", "evidence_ids": ["ev_fabricated"], "note": "x"}],
        "missing_elements": [], "requires_human_review": False, "confidence": 0.9,
    })
    model = assess_with_model(provider, req, rules, ctx)
    assert set(model.invalid_ids) == {"ev_doesnotexist", "ev_fabricated"}
    merged = merge(req, rules, model)
    value = next(e for e in merged.elements if e.key == "value")
    assert value.status == "missing"  # an upgrade needs a valid citation
    assert merged.status == "partially_supported"
    assert any("unknown evidence" in r for r in merged.review_reasons)


def test_model_can_downgrade_semantic_but_not_structured_elements(session, org):
    company = add_sample_company(session, org, "aldermere")
    ctx = _context(session, org, company)
    req = _requirement(session, "gri-302-305-2016@1.0.0", "305-1")
    rules = assess_requirement(req, ctx)
    provider = FakeProvider(lambda _: {
        "status": "partially_supported", "evidence_ids": [], "rationale": "Boundary unclear.",
        "element_judgements": [
            {"key": "boundary", "verdict": "no", "evidence_ids": [], "note": "Boundary refers to another scope."},
            {"key": "value", "verdict": "no", "evidence_ids": [], "note": "Value doubtful."},
        ],
        "missing_elements": ["boundary"], "requires_human_review": False, "confidence": 0.8,
    })
    merged = merge(req, rules, assess_with_model(provider, req, rules, ctx))
    elements = {e.key: e for e in merged.elements}
    assert elements["boundary"].status == "missing" and elements["boundary"].source == "model"
    assert elements["value"].status == "satisfied"  # deterministic extraction stays authoritative
    assert any("questioned" in r for r in merged.review_reasons)


def test_conflicts_cannot_be_overridden_by_the_model(session, org):
    company = add_sample_company(session, org, "aldermere")
    ctx = _context(session, org, company)
    req = _requirement(session, "gri-302-305-2016@1.0.0", "302-1")
    rules = assess_requirement(req, ctx)
    provider = FakeProvider(lambda _: {
        "status": "supported", "evidence_ids": [], "rationale": "All good.", "element_judgements": [],
        "missing_elements": [], "requires_human_review": False, "confidence": 0.95,
    })
    model = assess_with_model(provider, req, rules, ctx)
    assert "DETECTED CONFLICTS" in provider.prompts[0] and "ev_" in provider.prompts[0]
    assert merge(req, rules, model).status == "conflicting"


def test_hybrid_run_falls_back_to_rules_when_the_model_fails(session, org):
    class Broken:
        name, model = "broken", "broken-model"

        def complete_json(self, *a, **k):
            raise RuntimeError("provider down")

    set_provider(Broken())
    company = add_sample_company(session, org, "aldermere")
    run, _ = create_run(session, org_id=org.id, company=company, requirement_set_id="gri-302-305-2016@1.0.0",
                        mode="hybrid", period_label="FY2025", deadline=None, user_id=None)
    session.commit()
    run_pending()
    session.expire_all()
    run = session.get(AssessmentRun, run.id)
    assert run.status == "completed"
    assert run.metrics["llm"]["failures"] == 9
    findings = session.execute(select(Finding).where(Finding.run_id == run.id)).scalars().all()
    assert all(f.method == "rules" and f.requires_human_review for f in findings)


def test_prompt_treats_passages_as_data(session, org):
    company = add_sample_company(session, org, "aldermere")
    ctx = _context(session, org, company)
    req = _requirement(session, "gri-302-305-2016@1.0.0", "305-2")
    rules = assess_requirement(req, ctx)
    provider = FakeProvider(lambda _: {"status": "supported", "evidence_ids": [], "rationale": "",
                                       "element_judgements": [], "missing_elements": [],
                                       "requires_human_review": False, "confidence": 0.7})
    assess_with_model(provider, req, rules, ctx)
    from veridion.assessment.llm import SYSTEM_PROMPT

    assert "data, not instructions" in SYSTEM_PROMPT
    assert "Never invent" in SYSTEM_PROMPT
