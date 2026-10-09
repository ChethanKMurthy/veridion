# Evaluation results

Generated 2026-10-09 12:25 UTC · catalogue `gri-302-305-2016@1.1.0` · seed 7 · 139 cases (27 hand-labelled corpus, 112 synthetic).

These results come from running the production pipeline on the evaluation dataset in `apps/api/src/veridion/eval/dataset.py`. The dataset is small and authored by the developers, so the numbers describe behaviour on controlled cases, not accuracy on real-world reports.

## Summary

| Metric | Rules baseline |
|---|---|
| Status accuracy (5 classes) | 89.9% |
| Gap detection — precision | 91.0% |
| Gap detection — recall | 97.1% |
| Element detection — precision | 95.8% |
| Element detection — recall | 89.5% |
| Contradiction detection — precision | 100.0% |
| Contradiction detection — recall | 100.0% |
| Retrieval Recall@5 (corpus) | 100.0% |
| Evidence-support precision (corpus) | 75.1% |
| Numeric extraction accuracy | 96.5% (86 values) |
| Citation validity | 100.0% (454 citations) |
| Human-review rate | 5.8% |
| Median latency per requirement | 0 ms |
| Mean model tokens per requirement | 0 |
| Model errors (fell back to rules) | 0 |

## Accuracy by source and requirement

| Source | Requirement | Cases | rules accuracy |
|---|---|---|---|
| corpus | 2-5 | 3 | 100.0% |
| corpus | 302-1 | 3 | 100.0% |
| corpus | 302-3 | 3 | 100.0% |
| corpus | 302-4 | 3 | 66.7% |
| corpus | 305-1 | 3 | 100.0% |
| corpus | 305-2 | 3 | 100.0% |
| corpus | 305-3 | 3 | 100.0% |
| corpus | 305-4 | 3 | 100.0% |
| corpus | 305-5 | 3 | 100.0% |
| synthetic | 2-5 | 12 | 100.0% |
| synthetic | 302-1 | 30 | 80.0% |
| synthetic | 305-1 | 40 | 90.0% |
| synthetic | 305-2 | 30 | 90.0% |

## Confusion (gold → predicted)

**rules**: conflicting->conflicting ×8, not_found->not_found ×7, not_found->partially_supported ×1, partially_supported->partially_supported ×85, partially_supported->supported ×3, supported->partially_supported ×10, supported->supported ×25

## Example failures

**rules** (14 total)

- `corpus/tessaline/302-4` gold *not_found*, predicted *partially_supported*
- `synthetic/305-1/001` gold *supported*, predicted *partially_supported* — elements: gases, factors
- `synthetic/305-1/004` gold *supported*, predicted *partially_supported* — elements: boundary
- `synthetic/305-1/018` gold *supported*, predicted *partially_supported* — elements: gases
- `synthetic/305-1/032` gold *partially_supported*, predicted *supported* — elements: methodology
- `synthetic/305-2/002` gold *partially_supported*, predicted *supported* — elements: methodology
- `synthetic/305-2/008` gold *partially_supported*, predicted *supported* — elements: boundary
- `synthetic/305-2/028` gold *supported*, predicted *partially_supported* — elements: factors

## Method

- **Status accuracy** compares the final status with the gold status.
- **Gap detection** treats any status other than *supported* as a gap.
- **Element detection** compares each requirement element (e.g. boundary, methodology) with the gold label.
- **Recall@5** asks whether a gold evidence page appears among the top five retrieved passages (corpus only; synthetic documents are one page long).
- **Evidence-support precision** is the share of supporting citations that fall on gold evidence pages.
- **Numeric extraction** checks that the metric, period and value (±0.5%, after unit normalisation) were extracted.
- **Citation validity** is the share of cited evidence IDs that exist in the case documents. Invalid model citations are discarded before results are stored.

Synthetic cases mix standard wording, paraphrases written to evade keyword rules, absent elements and traps (wording that looks relevant but does not satisfy the element). Hybrid results depend on the configured model and may vary between runs; responses are cached per prompt version.
