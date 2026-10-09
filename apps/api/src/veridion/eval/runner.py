"""Run the evaluation suite and write a report.

    veridion eval run --mode rules
    veridion eval run --mode both --out ../../docs/evaluation.md --json eval-results.json

Each case is processed by the production pipeline (PDF parsing, extraction,
retrieval, rules and, in hybrid mode, the model) in an isolated database.
"""

from __future__ import annotations

import json
import statistics
import tempfile
import time
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from veridion.config import API_ROOT, configure, get_settings
from veridion.eval.dataset import SET_ID, Case, all_cases

STATUSES = ["supported", "partially_supported", "not_found", "conflicting", "human_review"]
SAMPLES = API_ROOT / "samples" / "pdfs"


def _render_pages(pages: list[str], title: str) -> bytes:
    from veridion.samples.content import SampleDocument, SamplePage
    from veridion.samples.generator import render_document

    return render_document(SampleDocument(slug="eval", title=title, doc_type="sustainability_report",
                                          period_label="FY2025", header=f"Example Company Ltd · {title}",
                                          pages=[SamplePage(p) for p in pages], published_on="2026-03-01"))


_BASE_SETTINGS = None


def _setup(tmp: Path, mode: str) -> None:
    from veridion import db, llm, storage

    global _BASE_SETTINGS
    if _BASE_SETTINGS is None:  # capture the real configuration before any mode overrides it
        _BASE_SETTINGS = get_settings()
    base = _BASE_SETTINGS
    configure(database_url=f"sqlite:///{tmp / f'eval-{mode}.db'}", storage_dir=str(tmp / "storage"),
              embedded_worker=False, llm_provider=base.llm_provider if mode == "hybrid" else "none",
              groq_api_key=base.groq_api_key, llm_model=base.llm_model, llm_base_url=base.llm_base_url,
              llm_api_key=base.llm_api_key, secret_key="eval", veridion_env="test")
    db.reset_engine()
    storage.reset_storage()
    llm.set_provider(None, explicit=False)
    db.create_all()


def run_mode(cases: list[Case], mode: str) -> list[dict]:
    from veridion.assessment.context import AssessmentContext
    from veridion.assessment.llm import assess_with_model
    from veridion.assessment.merge import merge, rules_only
    from veridion.assessment.rules import assess_requirement
    from veridion.catalog import load_catalog
    from veridion.db import session_factory
    from veridion.extraction.periods import fiscal_year
    from veridion.llm import get_provider
    from veridion.models import Company, Organization, RequirementSet
    from veridion.services.documents import create_document, current_documents, process_document

    results: list[dict] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        _setup(Path(tmpdir), mode)
        provider = get_provider() if mode == "hybrid" else None
        if mode == "hybrid" and provider is None:
            raise SystemExit("Hybrid evaluation needs a configured model provider (LLM_PROVIDER / API key).")
        session = session_factory()()
        load_catalog(session)
        org = Organization(name="Evaluation", slug="evaluation", plan="enterprise")
        session.add(org)
        session.commit()
        rs = session.get(RequirementSet, SET_ID)
        requirements = {r.code: r for r in rs.requirements}
        companies: dict[tuple, str] = {}

        for index, case in enumerate(cases, 1):
            key = tuple(d.slug or f"{case.id}#{i}" for i, d in enumerate(case.documents))
            if key not in companies:
                company = Company(org_id=org.id, name=case.id, fiscal_year_end=case.fiscal_year_end)
                session.add(company)
                session.flush()
                for i, d in enumerate(case.documents):
                    data = (SAMPLES / f"{d.slug}.pdf").read_bytes() if d.slug else _render_pages(d.pages or [], d.title)
                    doc, _ = create_document(session, org_id=org.id, company=company, data=data,
                                             filename=f"case-{i}.pdf", title=d.title, doc_type=d.doc_type,
                                             period_label="FY2025", published_on=None, uploaded_by=None)
                    process_document(session, doc)
                session.commit()
                companies[key] = company.id
            company = session.get(Company, companies[key])
            docs = current_documents(session, org.id, company.id)
            doc_index = {d.id: i for i, d in enumerate(sorted(docs, key=lambda d: d.created_at))}
            ctx = AssessmentContext.load(session, org.id, company.id, docs, fiscal_year(2025, company.fiscal_year_end))
            req = requirements[case.requirement_code]

            started = time.perf_counter()
            rules = assess_requirement(req, ctx)
            tokens = 0
            citation_invalid = 0
            citation_total = 0
            error = None
            if provider is not None:
                try:
                    model = assess_with_model(provider, req, rules, ctx)
                    merged = merge(req, rules, model)
                    usage = model.response.usage if model.response else {}
                    tokens = int((usage.get("prompt_tokens") or 0) + (usage.get("completion_tokens") or 0))
                    check = model.citation_check()
                    citation_invalid = len(check["invalid"])
                    citation_total = len(check["cited"]) + citation_invalid
                except Exception as exc:  # record the failure and score the rules-only result
                    merged, error = rules_only(rules), f"{type(exc).__name__}: {exc}"
            else:
                merged = rules_only(rules)
                citation_total = len({p for e in merged.elements for p in e.passage_ids})
            latency_ms = (time.perf_counter() - started) * 1000

            def loc(pid: str, ctx: AssessmentContext = ctx, doc_index: dict[str, int] = doc_index) -> tuple[int, int]:
                p = ctx.passages[pid]
                return doc_index[p.document_id], p.page

            top5 = [loc(h["passage_id"]) for h in rules.retrieval["hits"][:5]]
            supporting = [loc(pid) for e in merged.elements if e.status == "satisfied" for pid in e.passage_ids
                          if pid in ctx.passages]
            gold_pages = {tuple(p) for p in case.evidence_pages}
            value_hits = []
            for gv in case.values:
                found = any(m.metric_key == gv.metric_key and m.period_label == gv.period_label and
                            m.normalized_value is not None and abs(m.normalized_value - gv.value) <= 0.005 * abs(gv.value)
                            for m in ctx.metrics)
                value_hits.append({"metric": gv.metric_key, "period": gv.period_label, "value": gv.value, "found": found})
            results.append({
                "id": case.id, "source": case.source, "requirement": case.requirement_code, "gold": case.status,
                "predicted": merged.status, "rules_status": rules.status, "tags": case.tags,
                "gold_elements": case.elements,
                "predicted_elements": {e.key: e.status == "satisfied" for e in merged.elements
                                       if e.status != "not_applicable"},
                "gold_conflict": case.conflict, "predicted_conflict": bool(rules.conflicts),
                "requires_review": merged.requires_human_review,
                "recall_at_5": (bool(gold_pages & set(top5)) if gold_pages else None),
                "support_precision": (sum(1 for s in supporting if s in gold_pages) / len(supporting)
                                      if gold_pages and supporting else None),
                "citation_total": citation_total, "citation_invalid": citation_invalid,
                "values": value_hits, "latency_ms": round(latency_ms, 1), "tokens": tokens, "error": error,
                "rationale": merged.rationale[:400],
            })
            if index % 20 == 0:
                print(f"  [{mode}] {index}/{len(cases)} cases")
        session.close()
    return results


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def summarise(results: list[dict]) -> dict:
    n = len(results)
    correct = sum(r["gold"] == r["predicted"] for r in results)
    gap_tp = sum(r["gold"] != "supported" and r["predicted"] != "supported" for r in results)
    gap_fp = sum(r["gold"] == "supported" and r["predicted"] != "supported" for r in results)
    gap_fn = sum(r["gold"] != "supported" and r["predicted"] == "supported" for r in results)
    el_tp = el_fp = el_fn = 0
    for r in results:
        for key, gold in r["gold_elements"].items():
            pred = r["predicted_elements"].get(key)
            if pred is None:
                continue
            el_tp += gold and pred
            el_fp += (not gold) and pred
            el_fn += gold and not pred
    c_tp = sum(r["gold_conflict"] and r["predicted_conflict"] for r in results)
    c_fp = sum(not r["gold_conflict"] and r["predicted_conflict"] for r in results)
    c_fn = sum(r["gold_conflict"] and not r["predicted_conflict"] for r in results)
    recall5 = [r["recall_at_5"] for r in results if r["recall_at_5"] is not None and r["source"] == "corpus"]
    support = [r["support_precision"] for r in results if r["support_precision"] is not None and r["source"] == "corpus"]
    values = [v["found"] for r in results for v in r["values"]]
    cit_total = sum(r["citation_total"] for r in results)
    cit_invalid = sum(r["citation_invalid"] for r in results)
    confusion = Counter((r["gold"], r["predicted"]) for r in results)
    return {
        "cases": n,
        "status_accuracy": correct / n if n else 0.0,
        "gap": _prf(gap_tp, gap_fp, gap_fn),
        "elements": _prf(el_tp, el_fp, el_fn),
        "conflicts": _prf(c_tp, c_fp, c_fn),
        "recall_at_5": sum(recall5) / len(recall5) if recall5 else None,
        "support_precision": statistics.mean(support) if support else None,
        "numeric_accuracy": sum(values) / len(values) if values else None,
        "numeric_cases": len(values),
        "citation_validity": (cit_total - cit_invalid) / cit_total if cit_total else 1.0,
        "citations": cit_total,
        "review_rate": sum(r["requires_review"] for r in results) / n if n else 0.0,
        "latency_ms": statistics.median(r["latency_ms"] for r in results) if results else 0.0,
        "tokens": statistics.mean(r["tokens"] for r in results) if results else 0.0,
        "errors": sum(1 for r in results if r["error"]),
        "confusion": {f"{g}->{p}": c for (g, p), c in sorted(confusion.items())},
    }


def _fmt(v, pct=True) -> str:
    if v is None:
        return "—"
    return f"{v:.1%}" if pct else f"{v:,.0f}"


def render_report(runs: dict[str, list[dict]], seed: int) -> str:
    modes = list(runs)
    summaries = {m: summarise(r) for m, r in runs.items()}
    sources = defaultdict(int)
    for r in next(iter(runs.values())):
        sources[r["source"]] += 1
    head = "| Metric | " + " | ".join({"rules": "Rules baseline", "hybrid": "Hybrid (rules + model)"}[m] for m in modes) + " |"
    sep = "|---|" + "---|" * len(modes)

    def row(label, fn):
        return f"| {label} | " + " | ".join(fn(summaries[m]) for m in modes) + " |"

    lines = [
        "# Evaluation results",
        "",
        f"Generated {datetime.now(UTC):%Y-%m-%d %H:%M} UTC · catalogue `{SET_ID}` · seed {seed} · "
        f"{sum(sources.values())} cases ({sources['corpus']} hand-labelled corpus, {sources['synthetic']} synthetic).",
        "",
        "These results come from running the production pipeline on the evaluation dataset in "
        "`apps/api/src/veridion/eval/dataset.py`. The dataset is small and authored by the developers, so the "
        "numbers describe behaviour on controlled cases, not accuracy on real-world reports.",
        "",
        "## Summary",
        "",
        head, sep,
        row("Status accuracy (5 classes)", lambda s: _fmt(s["status_accuracy"])),
        row("Gap detection — precision", lambda s: _fmt(s["gap"][0])),
        row("Gap detection — recall", lambda s: _fmt(s["gap"][1])),
        row("Element detection — precision", lambda s: _fmt(s["elements"][0])),
        row("Element detection — recall", lambda s: _fmt(s["elements"][1])),
        row("Contradiction detection — precision", lambda s: _fmt(s["conflicts"][0])),
        row("Contradiction detection — recall", lambda s: _fmt(s["conflicts"][1])),
        row("Retrieval Recall@5 (corpus)", lambda s: _fmt(s["recall_at_5"])),
        row("Evidence-support precision (corpus)", lambda s: _fmt(s["support_precision"])),
        row("Numeric extraction accuracy", lambda s: f"{_fmt(s['numeric_accuracy'])} ({s['numeric_cases']} values)"),
        row("Citation validity", lambda s: f"{_fmt(s['citation_validity'])} ({s['citations']} citations)"),
        row("Human-review rate", lambda s: _fmt(s["review_rate"])),
        row("Median latency per requirement", lambda s: f"{s['latency_ms']:,.0f} ms"),
        row("Mean model tokens per requirement", lambda s: _fmt(s["tokens"], pct=False)),
        row("Model errors (fell back to rules)", lambda s: str(s["errors"])),
        "",
        "## Accuracy by source and requirement",
        "",
    ]
    groups = sorted({(r["source"], r["requirement"]) for r in next(iter(runs.values()))})
    lines += ["| Source | Requirement | Cases | " + " | ".join(f"{m} accuracy" for m in modes) + " |",
              "|---|---|---|" + "---|" * len(modes)]
    for source, req in groups:
        subset = {m: [r for r in runs[m] if r["source"] == source and r["requirement"] == req] for m in modes}
        lines.append(f"| {source} | {req} | {len(subset[modes[0]])} | " + " | ".join(
            _fmt(sum(r['gold'] == r['predicted'] for r in subset[m]) / len(subset[m])) for m in modes) + " |")
    lines += ["", "## Confusion (gold → predicted)", ""]
    for m in modes:
        lines.append(f"**{m}**: " + ", ".join(f"{k} ×{v}" for k, v in summaries[m]["confusion"].items()))
        lines.append("")
    lines += ["## Example failures", ""]
    for m in modes:
        failures = [r for r in runs[m] if r["gold"] != r["predicted"]][:8]
        lines.append(f"**{m}** ({sum(r['gold'] != r['predicted'] for r in runs[m])} total)")
        lines.append("")
        for r in failures:
            wrong = [k for k, g in r["gold_elements"].items() if r["predicted_elements"].get(k) not in (None, g)]
            detail = f" — elements: {', '.join(wrong)}" if wrong else ""
            lines.append(f"- `{r['id']}` gold *{r['gold']}*, predicted *{r['predicted']}*{detail}")
        lines.append("")
    lines += [
        "## Method",
        "",
        "- **Status accuracy** compares the final status with the gold status.",
        "- **Gap detection** treats any status other than *supported* as a gap.",
        "- **Element detection** compares each requirement element (e.g. boundary, methodology) with the gold label.",
        "- **Recall@5** asks whether a gold evidence page appears among the top five retrieved passages "
        "(corpus only; synthetic documents are one page long).",
        "- **Evidence-support precision** is the share of supporting citations that fall on gold evidence pages.",
        "- **Numeric extraction** checks that the metric, period and value (±0.5%, after unit normalisation) "
        "were extracted.",
        "- **Citation validity** is the share of cited evidence IDs that exist in the case documents. Invalid "
        "model citations are discarded before results are stored.",
        "",
        "Synthetic cases mix standard wording, paraphrases written to evade keyword rules, absent elements and "
        "traps (wording that looks relevant but does not satisfy the element). Hybrid results depend on the "
        "configured model and may vary between runs; responses are cached per prompt version.",
    ]
    return "\n".join(lines) + "\n"


def web_summary(runs: dict[str, list[dict]], *, sampled: bool) -> dict:
    """Compact metrics for the website's methodology page."""
    first = next(iter(runs.values()))
    out: dict = {
        "generated_at": datetime.now(UTC).isoformat(),
        "set_id": SET_ID,
        "cases": len(first),
        "corpus_cases": sum(1 for r in first if r["source"] == "corpus"),
        "synthetic_cases": sum(1 for r in first if r["source"] == "synthetic"),
        "sampled": sampled,
        "modes": {},
    }
    for mode, results in runs.items():
        s = summarise(results)
        out["modes"][mode] = {
            "status_accuracy": s["status_accuracy"], "gap_precision": s["gap"][0], "gap_recall": s["gap"][1],
            "element_precision": s["elements"][0], "element_recall": s["elements"][1],
            "conflict_precision": s["conflicts"][0], "conflict_recall": s["conflicts"][1],
            "recall_at_5": s["recall_at_5"], "support_precision": s["support_precision"],
            "numeric_accuracy": s["numeric_accuracy"], "citation_validity": s["citation_validity"],
            "review_rate": s["review_rate"], "latency_ms": s["latency_ms"], "tokens": s["tokens"], "errors": s["errors"],
        }
    return out


def main(args) -> None:
    cases = all_cases()
    if args.limit:
        # Keep every hand-labelled corpus case and an evenly spaced sample of synthetic cases.
        corpus = [c for c in cases if c.source == "corpus"]
        synthetic = [c for c in cases if c.source == "synthetic"]
        k = max(0, args.limit - len(corpus))
        step = max(1, len(synthetic) / k) if k else len(synthetic) + 1
        sample = [synthetic[int(i * step)] for i in range(min(k, len(synthetic)))]
        cases = corpus + sample
    modes = ["rules", "hybrid"] if args.mode == "both" else [args.mode]
    runs: dict[str, list[dict]] = {}
    for mode in modes:
        print(f"Running {len(cases)} cases in {mode} mode…")
        runs[mode] = run_mode(cases, mode)
        s = summarise(runs[mode])
        print(f"  status accuracy {s['status_accuracy']:.1%} · gap P/R {s['gap'][0]:.1%}/{s['gap'][1]:.1%} · "
              f"elements P/R {s['elements'][0]:.1%}/{s['elements'][1]:.1%} · conflicts P/R "
              f"{s['conflicts'][0]:.1%}/{s['conflicts'][1]:.1%}")
    report = render_report(runs, seed=7)
    if args.limit:
        report = report.replace("## Summary", f"Sampled run: all corpus cases plus an evenly spaced sample of synthetic "
                                f"cases ({len(cases)} of {len(all_cases())}), to stay within the model provider's "
                                "free-tier limits. Run `veridion eval run --mode both` for the full set.\n\n## Summary", 1)
    if args.out:
        Path(args.out).write_text(report)
        print(f"Report written to {args.out}")
    else:
        print(report)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(runs, indent=1, default=str))
    if getattr(args, "web_summary", None):
        Path(args.web_summary).write_text(json.dumps(web_summary(runs, sampled=bool(args.limit)), indent=1))
        print(f"Web summary written to {args.web_summary}")
