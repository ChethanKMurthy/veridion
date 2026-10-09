"""Assessment reports and exportable evidence packages."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from veridion import __version__
from veridion.api import serializers as S
from veridion.assessment.context import short_doc_name
from veridion.models import (
    Action,
    AssessmentRun,
    Company,
    Document,
    Finding,
    FindingEvidence,
    Passage,
    Requirement,
    RequirementSet,
    Review,
)

STATUS_LABEL = {
    "supported": "Supported",
    "partially_supported": "Partially supported",
    "not_found": "Evidence not found",
    "conflicting": "Conflicting evidence",
    "human_review": "Human review required",
}

LIMITATIONS = [
    "Findings describe the evidence available in the documents provided. Absence of evidence is not "
    "evidence of non-compliance.",
    "Requirement summaries are Veridion's paraphrases of the referenced standards; consult the official text.",
    "The completeness score is an internal evidence-completeness measure, not a compliance score or legal opinion.",
    "Values are extracted automatically and should be verified against the source before external use.",
]


def finding_trail(db: Session, finding: Finding) -> dict:
    """The full evidence trail for one finding: requirement → evidence → rationale → gap → action."""
    req = db.get(Requirement, finding.requirement_id)
    assert req is not None
    links = db.execute(select(FindingEvidence).where(FindingEvidence.finding_id == finding.id)
                       .order_by(FindingEvidence.rank)).scalars().all()
    passages = {p.id: p for p in db.execute(
        select(Passage).where(Passage.id.in_([link.passage_id for link in links]))).scalars()} if links else {}
    doc_ids = {p.document_id for p in passages.values()}
    docs = {d.id: d for d in db.execute(select(Document).where(Document.id.in_(doc_ids))).scalars()} if doc_ids else {}
    # Passages cited by elements but not linked (e.g. context passages) — fetch for completeness.
    element_pids = {pid for e in finding.element_results for pid in e.get("passage_ids", []) + e.get("context_passage_ids", [])}
    missing = element_pids - set(passages)
    if missing:
        for p in db.execute(select(Passage).where(Passage.id.in_(missing))).scalars():
            passages[p.id] = p
            if p.document_id not in docs:
                d = db.get(Document, p.document_id)
                if d:
                    docs[d.id] = d
    evidence = []
    for link in links:
        p = passages.get(link.passage_id)
        if p is None:
            continue
        evidence.append({"role": link.role, "element_keys": link.element_keys, "note": link.note, "score": link.score,
                         "passage": S.passage(p, docs.get(p.document_id))})
    reviews = db.execute(select(Review).where(Review.finding_id == finding.id)
                         .order_by(Review.created_at)).scalars().all()
    actions = db.execute(select(Action).where(Action.finding_id == finding.id)
                         .order_by(Action.priority_score.desc())).scalars().all()
    run = db.get(AssessmentRun, finding.run_id)
    history_rows = db.execute(
        select(Finding, AssessmentRun).join(AssessmentRun, AssessmentRun.id == Finding.run_id)
        .where(Finding.company_id == finding.company_id, Finding.requirement_code == finding.requirement_code,
               Finding.org_id == finding.org_id, AssessmentRun.status == "completed")
        .order_by(AssessmentRun.created_at.desc()).limit(12)
    ).all()
    return {
        "finding": {
            **S.finding_summary(finding, req, reviews=list(reviews), evidence_count=len(evidence)),
            "element_results": finding.element_results, "rules_rationale": finding.rules_rationale,
            "llm_output": finding.llm_output, "citation_check": finding.citation_check,
            "retrieval": finding.retrieval,
        },
        "requirement": S.requirement(req),
        "run": S.run(run) if run else None,
        "evidence": evidence,
        "passages": {pid: S.passage(p, docs.get(p.document_id)) for pid, p in passages.items()},
        "reviews": [S.review(r) for r in reviews],
        "actions": [S.action(a) for a in actions],
        "history": [{"finding_id": f.id, "run_id": r.id, "status": f.status, "completeness": f.completeness,
                     "requirement_set_id": r.requirement_set_id, "mode": r.mode, "created_at": S.iso(r.created_at)}
                    for f, r in history_rows],
    }


def run_findings(db: Session, run: AssessmentRun) -> list[dict]:
    findings = db.execute(select(Finding).where(Finding.run_id == run.id)).scalars().all()
    if not findings:
        return []
    reqs = {r.id: r for r in db.execute(
        select(Requirement).where(Requirement.id.in_({f.requirement_id for f in findings}))).scalars()}
    reviews: dict[str, list[Review]] = {}
    for rv in db.execute(select(Review).where(Review.finding_id.in_([f.id for f in findings]))
                         .order_by(Review.created_at)).scalars():
        reviews.setdefault(rv.finding_id, []).append(rv)
    links = db.execute(select(FindingEvidence).where(FindingEvidence.finding_id.in_([f.id for f in findings]))
                       .order_by(FindingEvidence.rank)).scalars().all()
    by_finding: dict[str, list[FindingEvidence]] = {}
    for link in links:
        by_finding.setdefault(link.finding_id, []).append(link)
    passage_ids = {link.passage_id for link in links}
    passages = {p.id: p for p in db.execute(select(Passage).where(Passage.id.in_(passage_ids))).scalars()} \
        if passage_ids else {}
    docs = {d.id: d for d in db.execute(
        select(Document).where(Document.id.in_({p.document_id for p in passages.values()}))).scalars()} \
        if passages else {}
    out = []
    for f in findings:
        req = reqs[f.requirement_id]
        f_links = [link for link in by_finding.get(f.id, []) if link.role != "related"]
        primary = None
        if f_links:
            p = passages.get(f_links[0].passage_id)
            if p is not None:
                d = docs.get(p.document_id)
                primary = {"passage_id": p.id, "document_id": p.document_id, "page": p.page,
                           "document": short_doc_name(d) if d else None,
                           "period_label": d.period_label if d else None, "text": p.text[:240],
                           "bbox": p.bbox, "role": f_links[0].role}
        out.append({**S.finding_summary(f, req, reviews=reviews.get(f.id, []), evidence_count=len(f_links),
                                        primary=primary),
                    "ordinal": req.ordinal})
    out.sort(key=lambda r: r["ordinal"])
    return out


def report_data(db: Session, run: AssessmentRun) -> dict:
    company = db.get(Company, run.company_id)
    rs = db.get(RequirementSet, run.requirement_set_id)
    assert company is not None and rs is not None
    findings = run_findings(db, run)
    trails = {f["id"]: finding_trail(db, db.get(Finding, f["id"])) for f in findings}
    actions = db.execute(select(Action).where(Action.run_id == run.id, Action.status.not_in(["dismissed"]))
                         .order_by(Action.priority_score.desc())).scalars().all()
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "generator": f"Veridion {__version__}",
        "company": S.company(company),
        "run": S.run(run, set_title=rs.title),
        "requirement_set": S.requirement_set(rs),
        "findings": findings,
        "trails": trails,
        "actions": [S.action(a) for a in actions],
        "limitations": LIMITATIONS,
    }


def evidence_package(db: Session, run: AssessmentRun) -> dict:
    """A self-contained, machine-readable record of the run for audit or archival."""
    data = report_data(db, run)
    docs = run.input_manifest.get("documents", [])
    return {
        "format": "veridion.evidence-package/1",
        "generated_at": data["generated_at"],
        "generator": data["generator"],
        "company": data["company"],
        "run": data["run"],
        "requirement_set": data["requirement_set"],
        "documents": docs,
        "findings": [{
            **f,
            "elements": data["trails"][f["id"]]["finding"]["element_results"],
            "evidence": [{"role": e["role"], "element_keys": e["element_keys"], "passage_id": e["passage"]["id"],
                          "document_id": e["passage"]["document_id"], "page": e["passage"]["page"],
                          "text": e["passage"]["text"], "bbox": e["passage"]["bbox"]}
                         for e in data["trails"][f["id"]]["evidence"]],
            "reviews": data["trails"][f["id"]]["reviews"],
        } for f in data["findings"]],
        "actions": data["actions"],
        "limitations": data["limitations"],
    }


def findings_csv(db: Session, run: AssessmentRun) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["requirement", "title", "status", "effective_status", "review_state", "completeness",
                     "confidence", "priority", "missing_elements", "primary_source", "rationale", "method",
                     "requirement_set", "run_id"])
    for f in run_findings(db, run):
        src = f["primary_evidence"]
        writer.writerow([
            f["display_code"], f["title"], STATUS_LABEL[f["status"]],
            STATUS_LABEL.get(f["review"]["effective_status"], f["review"]["effective_status"]), f["review"]["state"],
            f"{f['completeness']:.2f}", f"{f['confidence']:.2f}", f["priority"].get("P", ""),
            "; ".join(f["missing_elements"]), f"{src['document']} p.{src['page']}" if src else "",
            f["rationale"], f["method"], run.requirement_set_id, run.id,
        ])
    return buf.getvalue()


def findings_markdown(db: Session, run: AssessmentRun) -> str:
    data = report_data(db, run)
    c, r = data["company"], data["run"]
    lines = [
        f"# {c['name']} — evidence assessment",
        "",
        f"*{data['requirement_set']['title']}* · catalogue `{r['requirement_set_id']}` · period {r['period_label']} · "
        f"run `{r['id']}` ({r['mode']}) · generated {data['generated_at'][:16].replace('T', ' ')} UTC",
        "",
    ]
    if c.get("is_sample"):
        lines += ["> Fictional sample company. Figures are invented for demonstration.", ""]
    lines += ["## Summary", "", "| Requirement | Status | Completeness | Priority |", "|---|---|---|---|"]
    for f in data["findings"]:
        lines.append(f"| {f['display_code']} {f['title']} | {STATUS_LABEL[f['status']]} | "
                     f"{f['completeness']:.0%} | {f['priority'].get('P', 0):.2f} |")
    lines += ["", "## Findings", ""]
    for f in data["findings"]:
        trail = data["trails"][f["id"]]
        lines += [f"### {f['display_code']} — {f['title']}", "", f"**{STATUS_LABEL[f['status']]}** · completeness "
                  f"{f['completeness']:.0%} · confidence {f['confidence']:.2f}", "", f["rationale"], ""]
        for e in trail["evidence"][:4]:
            p = e["passage"]
            doc = p["document"]["short_name"] if p.get("document") else p["document_id"]
            lines.append(f"- *{e['role']}* — {doc}, p.{p['page']}: “{p['text'][:220]}”")
        if f["missing_elements"]:
            lines += ["", "Missing: " + "; ".join(f["missing_elements"])]
        lines.append("")
    if data["actions"]:
        lines += ["## Recommended actions", ""]
        for a in data["actions"]:
            lines.append(f"1. **{a['title']}** ({a['requirement_code']}, priority {a['priority_score']:.2f}, "
                         f"effort {a['effort']}) — {a['detail']}")
        lines.append("")
    lines += ["## Limitations", ""] + [f"- {item}" for item in data["limitations"]]
    return "\n".join(lines) + "\n"
