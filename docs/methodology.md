# Assessment methodology

This document explains exactly how Veridion turns documents into findings. It is written for analysts who need to rely on the results and for engineers who change the engine. Where it states a number or a rule, that number or rule is what the code does; the source files are named so it can be checked.

## What a finding means

A finding says how well **the documents provided** evidence one requirement. It is not a determination that a company complies with a standard, and absence of evidence in the uploaded documents is not evidence of non-compliance. Every finding records the catalogue version, documents, rules version and (if used) the model and prompt version that produced it.

| Status | Meaning |
|---|---|
| **Supported** | Every applicable element of the requirement is evidenced by a cited passage. |
| **Partially supported** | At least one element is evidenced and at least one is missing. |
| **Not found** | No element is evidenced in the documents provided. |
| **Conflicting** | The documents report materially different values for the same metric and period (see [Conflicts](#conflicts)). Conflicts are never resolved automatically. |
| **Needs human review** | The evidence cannot be judged reliably without a person, for example when it rests on low-confidence OCR text or when the rules and the model disagree sharply. |

Reviewers can accept a finding, override its status with a reason, or comment. Reviews are stored alongside the original finding; they never rewrite it.

## Requirement catalogues

Requirements live in versioned YAML files under `apps/api/catalog/`. Each set has a key and semantic version (`gri-302-305-2016@1.1.0`), effective dates, a review status (`reviewed` or `draft`), source references and a changelog. Requirement summaries are Veridion's paraphrases written to drive evidence checks; they are not the authoritative text of any standard.

Each requirement is broken into **elements**: the individual things a disclosure must contain. Each element has a weight (importance within the requirement) and a typed check:

| Check | Satisfied when |
|---|---|
| `metric` | A value for the named metric is extracted for the assessment period |
| `metric_period` | That value's period is stated in the text, not only inferred |
| `pattern` | Wording matching the patterns is present, optionally near context terms |
| `any_of` | Any nested check is satisfied |
| `conditional` | The element applies only when its `when` check is satisfied; otherwise it is not applicable |

A catalogue version is immutable once an assessment has used it: if its content changes without a new version number, loading fails. Analysts can also mark a requirement as not applicable for a company, with a rationale; excluded requirements are listed on the run.

Current catalogues:

| Set | Status | Scope |
|---|---|---|
| `gri-302-305-2016` 1.0.0 and 1.1.0 | Reviewed, in force for reports published before 1 January 2027 | GRI 302-1, 302-3, 302-4, 305-1 to 305-5 and GRI 2-5 (external assurance) |
| `gri-102-103-2025` 0.1.0 | Draft, upcoming | Early-adoption subset of GRI 102: Climate Change 2025 and GRI 103: Energy 2025 |

## Document processing

`apps/api/src/veridion/pipeline/pdf.py`

1. **Text layer.** PyMuPDF reads text with positions. Ligatures and compatibility characters are normalised (NFKC).
2. **OCR.** A page with almost no text but an embedded image is treated as scanned: it is rendered at 300 DPI and read with Tesseract. Each OCR passage carries the mean word confidence.
3. **Tables.** Ruled tables are detected and split into rows, so a row ("Scope 1 · 2025: 48,210 · 2024: 51,030") is a passage of its own. Tables in scanned pages are rebuilt from aligned text lines.
4. **Running headers and footers** that repeat across pages are removed.
5. **Passages.** Text is segmented into headings, paragraphs and table rows. Each passage keeps its page, bounding box and section path, and gets a deterministic identifier (a hash of document, page, position and text), so re-processing yields the same citations.

## Metric extraction

`apps/api/src/veridion/extraction/`

Values are extracted deterministically from text and table rows for a fixed set of metrics: Scope 1, Scope 2 (location-based, market-based or unstated), Scope 3, combined and total emissions, biogenic CO2, emission reductions, total energy, fuel and electricity consumption, renewable share, energy reductions, water withdrawal and consumption, waste generated, and emissions and energy intensity.

- **Units** are normalised within a family: emissions to tCO2e (kt, Mt, thousand tonnes, '000 t), energy to MWh (1 MWh = 3.6 GJ; kWh, GWh, MJ, TJ, PJ), volume to m³, mass to tonnes. The reported value and unit are always kept beside the normalised one.
- **Numbers** handle thousands separators, spaced thousands, decimals, and scale words including thousand, million, billion, lakh and crore.
- **Periods** are resolved to the company's fiscal year end (a March year end makes "2024/25" FY2025). Comparative columns, "(2024: x)" labels, and base-year statements ("in the 2019 base year…") are assigned to their own periods rather than the current one.
- Component rows (for example a single fuel within an energy table) are not mistaken for totals.

## Retrieval

`apps/api/src/veridion/retrieval/`

For each requirement, passages are ranked with BM25 (k1 = 1.4, b = 0.75) over the requirement's search terms, with additional weight for exact phrases, passages that contain an extracted value for the requirement's metrics, and relevant sections. Each hit records why it matched (terms, phrases, metric, section), which the interface shows as "why this passage".

## Rules assessment

`apps/api/src/veridion/assessment/rules.py`

Each element's check is evaluated against the extracted values and retrieved passages. Then:

**Completeness** is the weighted share of applicable elements that are evidenced:

```
C = Σ wᵢ·sᵢ / Σ wᵢ      sᵢ = 1 if element i is evidenced, else 0; non-applicable elements are excluded
```

**Status** follows from completeness unless a conflict exists: C = 1 → supported; 0 < C < 1 → partially supported; C = 0 → not found.

### Conflicts

For each metric the requirement depends on, all values extracted for the assessment period are compared after unit normalisation. If the highest exceeds the lowest by more than **1%** of the lower value, the requirement is conflicting and both sources are cited. The demo's example: a sustainability report states total energy of 412,300 MWh while the annual report states 1,532,000 GJ (425,556 MWh), a 3.2% difference.

### Confidence and review triggers

Confidence averages per-element scores: evidenced elements score the confidence of their best passage (1.0 for text, the OCR confidence for scanned text, reduced by 20% for weak matches); missing elements score 0.75, because absence is checked across every passage but wording can vary. Conflicts reduce confidence by 15%. Confidence is capped at 0.95.

A finding is routed to human review when:

- values conflict (status stays *conflicting*);
- an element rests only on OCR text with confidence below 0.85 (status becomes *needs human review*);
- the model and the rules disagree in the ways described below.

## Model-assisted assessment (optional)

`apps/api/src/veridion/assessment/llm.py`, `merge.py`

In *rules + model* mode, a language model reviews each requirement after the rules have run. It receives the requirement, its elements, the rules' element results and at most 12 candidate passages (up to 600 characters each), chosen from the rules' evidence and the top retrieval hits. The prompt treats passages as data, not instructions. The model must answer in a strict JSON schema with a verdict per element (`yes`, `no`, `unclear`), the passage IDs it relied on, an overall status, a confidence and a rationale. Temperature is 0, responses are cached by a hash of model, prompt version and inputs, and the model can only cite IDs it was given: any other ID is discarded and the finding is flagged.

The two results are merged by a fixed policy:

| Situation | Outcome |
|---|---|
| Structured element (a value or its period) and the model disagrees | The rules result stands; the finding is flagged for review |
| Wording element matched by patterns, model says the wording does not establish it | Element becomes missing; the override and the model's reason are recorded |
| Element missing, model says it is present and cites a valid passage | Element becomes satisfied, marked weak and attributed to the model; structured elements are also flagged for review |
| Model is unsure about an element | Noted on structured elements when the model's overall confidence is at least 0.6; otherwise flagged for review |
| Rules find nothing, model finds related disclosure with valid citations | Status becomes partially supported, with the related passages cited |
| Overall statuses two steps apart (supported vs not found) | Status becomes needs human review |
| Conflict detected by the rules | Always kept; the model cannot override it |
| Model reports a contradiction the value checks did not confirm | Flagged for review; status unchanged |

Every override is stored on the element with its source, so the interface can show exactly what the model changed. If the model call fails, the requirement falls back to the rules result and the run records the failure.

## Remediation priority

`apps/api/src/veridion/assessment/priority.py`

Gaps become actions ranked by **P = I × G × U**. This is a heuristic for ordering work, not a regulatory score; all three components are stored and shown.

| Component | Values |
|---|---|
| I, importance | Catalogue importance 1, 2 or 3 → 0.4, 0.7 or 1.0 |
| G, gap size | Not found 1.0 · conflicting 0.8 · needs review 0.5 · partially supported 1 − C (at least 0.1) · supported 0 |
| U, urgency | Deadline within 30 days 1.0 · 90 days 0.8 · 180 days 0.6 · later 0.4 · no deadline 0.5 |

Actions persist across runs. A later run that no longer shows the gap marks the action as closed by that run; a gap that returns reopens it.

## Peer benchmarking

`apps/api/src/veridion/benchmarking/`

Peer tables show each company's value in a common unit with its period and source page. A metric that is not disclosed is shown as not disclosed, never as zero. Every cell carries comparability notes:

| Note | Raised when |
|---|---|
| Period | The period is inferred rather than stated, or differs from the focal company's |
| Boundary | The consolidation approach differs or is not stated |
| Method | Scope 2 method is not stated |
| Converted | The value was converted from another unit |
| OCR | The value was read from a scanned page |
| Conflict | The company's own documents disagree on the value |
| Denominator / scope | Intensity denominators or the scope of a share differ |

A row is labelled *directly comparable* only when at least two companies disclose, units agree, and no period, boundary, method, conflict or denominator note applies.

## Reproducibility and change

Each run stores the SHA-256 of every input document, the catalogue version and content hash, and the pipeline, extraction, rules and prompt versions. Runs are never edited. Comparing two runs attributes each changed finding to its causes: the catalogue was revised, documents were added or replaced, or the method changed (rules version, prompt, model or mode). When a document is replaced by a newer version, findings that cite the old one are marked stale until a new run reassesses them.

## Evaluation

The labelled evaluation suite (`apps/api/src/veridion/eval/`) contains 27 hand-labelled cases on the sample corpus and 112 synthetic cases built from paraphrases, absent disclosures and traps such as base-year figures and component rows. Current results are in [evaluation.md](evaluation.md) (rules vs rules + model on 45 cases) and [evaluation-rules-full.md](evaluation-rules-full.md) (rules on all 139). The dataset is small and authored by the developers, so the numbers describe behaviour on controlled cases, not accuracy on real-world reports. Run it with `make eval`.

## Known limitations

- Catalogues cover a focused set of GRI energy and emissions disclosures. Other frameworks (ESRS, ISSB/IFRS S2, SASB) need their own catalogues and review.
- Wording checks are pattern-based; unusual phrasing can be missed by the rules alone (the model mode exists partly for this).
- Extraction is tuned to report-style PDFs in English. Spreadsheets, images without OCR-able text and other languages are not yet supported.
- Values are compared within one company's documents for conflicts; restatements across years are reported as different periods, not reconciled.
- Synthetic evaluation cases are generated from templates written by the same team that wrote the rules, which flatters recall.
