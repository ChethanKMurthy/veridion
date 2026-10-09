"""Change-impact analysis between two assessment runs.

Explains *why* results changed: a revised requirement, different documents,
or a different method (pipeline, rules, prompt or model version).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from veridion.models import AssessmentRun, Finding, FindingEvidence

_VERSION_FIELDS = ("pipeline_version", "extraction_version", "rules_version", "prompt_version", "llm_model", "mode")


def _findings(session: Session, run_id: str) -> dict[str, Finding]:
    return {f.requirement_code: f for f in session.execute(select(Finding).where(Finding.run_id == run_id)).scalars()}


def _evidence(session: Session, finding_id: str) -> set[str]:
    return set(session.execute(
        select(FindingEvidence.passage_id).where(FindingEvidence.finding_id == finding_id,
                                                 FindingEvidence.role != "related")
    ).scalars())


def diff_runs(session: Session, before: AssessmentRun, after: AssessmentRun) -> dict:
    docs_before = {d["lineage_id"]: d for d in before.input_manifest.get("documents", [])}
    docs_after = {d["lineage_id"]: d for d in after.input_manifest.get("documents", [])}
    doc_changes = []
    for lineage, d in docs_after.items():
        prior = docs_before.get(lineage)
        if prior is None:
            doc_changes.append({"change": "added", "title": d["title"], "document_id": d["id"]})
        elif prior["sha256"] != d["sha256"] or prior["id"] != d["id"]:
            doc_changes.append({"change": "replaced", "title": d["title"], "document_id": d["id"],
                                "from_version": prior["version"], "to_version": d["version"]})
    for lineage, d in docs_before.items():
        if lineage not in docs_after:
            doc_changes.append({"change": "removed", "title": d["title"], "document_id": d["id"]})

    version_changes = [
        {"field": f, "before": getattr(before, f), "after": getattr(after, f)}
        for f in _VERSION_FIELDS if getattr(before, f) != getattr(after, f)
    ]
    req_before = before.input_manifest.get("requirements", {})
    req_after = after.input_manifest.get("requirements", {})
    set_changed = before.requirement_set_id != after.requirement_set_id

    fb, fa = _findings(session, before.id), _findings(session, after.id)
    items = []
    for code in sorted(set(fb) | set(fa)):
        a, b = fb.get(code), fa.get(code)
        causes = []
        if code not in req_before:
            causes.append("requirement added")
        elif code not in req_after:
            causes.append("requirement removed or marked not applicable")
        elif req_before[code] != req_after[code]:
            causes.append("requirement revised")
        ev_before = _evidence(session, a.id) if a else set()
        ev_after = _evidence(session, b.id) if b else set()
        if doc_changes and ev_before != ev_after:
            causes.append("documents changed")
        if version_changes:
            causes.append("method changed")
        status_changed = (a.status if a else None) != (b.status if b else None)
        completeness_changed = round(a.completeness if a else 0, 3) != round(b.completeness if b else 0, 3)
        if not (status_changed or completeness_changed or ev_before != ev_after):
            continue
        elements_before = {e["key"]: e["status"] for e in (a.element_results if a else [])}
        elements_after = {e["key"]: e["status"] for e in (b.element_results if b else [])}
        element_changes = [
            {"key": k, "before": elements_before.get(k), "after": elements_after.get(k)}
            for k in sorted(set(elements_before) | set(elements_after))
            if elements_before.get(k) != elements_after.get(k)
        ]
        items.append({
            "requirement_code": code,
            "before": {"status": a.status, "completeness": a.completeness, "finding_id": a.id} if a else None,
            "after": {"status": b.status, "completeness": b.completeness, "finding_id": b.id} if b else None,
            "status_changed": status_changed,
            "evidence_added": sorted(ev_after - ev_before),
            "evidence_removed": sorted(ev_before - ev_after),
            "element_changes": element_changes,
            "causes": causes or ["evidence selection changed"],
        })
    summary_bits = []
    status_changes = [i for i in items if i["status_changed"]]
    if status_changes:
        summary_bits.append(f"{len(status_changes)} finding{'s' if len(status_changes) != 1 else ''} changed status")
    if set_changed:
        b_key, _, b_ver = before.requirement_set_id.partition("@")
        a_key, _, a_ver = after.requirement_set_id.partition("@")
        summary_bits.append(f"catalogue revised from v{b_ver} to v{a_ver}" if a_key == b_key
                            else f"catalogue changed from {before.requirement_set_id} to {after.requirement_set_id}")
    if doc_changes:
        summary_bits.append(f"{len(doc_changes)} document change{'s' if len(doc_changes) != 1 else ''}")
    return {
        "before_run_id": before.id, "after_run_id": after.id,
        "requirement_set_changed": set_changed,
        "requirement_sets": {"before": before.requirement_set_id, "after": after.requirement_set_id},
        "document_changes": doc_changes, "version_changes": version_changes, "items": items,
        "summary": "; ".join(summary_bits) or "No changes in findings",
    }
