# Evaluation results

Generated 2026-10-09 12:15 UTC · catalogue `gri-302-305-2016@1.1.0` · seed 7 · 45 cases (27 hand-labelled corpus, 18 synthetic).

These results come from running the production pipeline on the evaluation dataset in `apps/api/src/veridion/eval/dataset.py`. The dataset is small and authored by the developers, so the numbers describe behaviour on controlled cases, not accuracy on real-world reports.

Sampled run: all corpus cases plus an evenly spaced sample of synthetic cases (45 of 139), to stay within the model provider's free-tier limits. Run `veridion eval run --mode both` for the full set.

## Summary

| Metric | Rules baseline | Hybrid (rules + model) |
|---|---|---|
| Status accuracy (5 classes) | 93.3% | 93.3% |
| Gap detection — precision | 94.1% | 97.0% |
| Gap detection — recall | 100.0% | 100.0% |
| Element detection — precision | 100.0% | 98.9% |
| Element detection — recall | 88.8% | 96.6% |
| Contradiction detection — precision | 100.0% | 100.0% |
| Contradiction detection — recall | 100.0% | 100.0% |
| Retrieval Recall@5 (corpus) | 100.0% | 100.0% |
| Evidence-support precision (corpus) | 75.1% | 76.5% |
| Numeric extraction accuracy | 100.0% (31 values) | 100.0% (31 values) |
| Citation validity | 100.0% (132 citations) | 100.0% (192 citations) |
| Human-review rate | 8.9% | 13.3% |
| Median latency per requirement | 0 ms | 2,611 ms |
| Mean model tokens per requirement | 0 | 2,181 |
| Model errors (fell back to rules) | 0 | 0 |

## Accuracy by source and requirement

| Source | Requirement | Cases | rules accuracy | hybrid accuracy |
|---|---|---|---|---|
| corpus | 2-5 | 3 | 100.0% | 100.0% |
| corpus | 302-1 | 3 | 100.0% | 100.0% |
| corpus | 302-3 | 3 | 100.0% | 100.0% |
| corpus | 302-4 | 3 | 66.7% | 66.7% |
| corpus | 305-1 | 3 | 100.0% | 100.0% |
| corpus | 305-2 | 3 | 100.0% | 100.0% |
| corpus | 305-3 | 3 | 100.0% | 100.0% |
| corpus | 305-4 | 3 | 100.0% | 100.0% |
| corpus | 305-5 | 3 | 100.0% | 66.7% |
| synthetic | 2-5 | 1 | 100.0% | 100.0% |
| synthetic | 302-1 | 5 | 100.0% | 100.0% |
| synthetic | 305-1 | 7 | 85.7% | 100.0% |
| synthetic | 305-2 | 5 | 80.0% | 80.0% |

## Confusion (gold → predicted)

**rules**: conflicting->conflicting ×4, not_found->not_found ×7, not_found->partially_supported ×1, partially_supported->partially_supported ×20, supported->partially_supported ×2, supported->supported ×11

**hybrid**: conflicting->conflicting ×4, not_found->not_found ×6, not_found->partially_supported ×2, partially_supported->partially_supported ×20, supported->partially_supported ×1, supported->supported ×12

## Example failures

**rules** (3 total)

- `corpus/tessaline/302-4` gold *not_found*, predicted *partially_supported*
- `synthetic/305-1/018` gold *supported*, predicted *partially_supported* — elements: gases
- `synthetic/305-2/028` gold *supported*, predicted *partially_supported* — elements: factors

**hybrid** (3 total)

- `corpus/tessaline/302-4` gold *not_found*, predicted *partially_supported*
- `corpus/corvane/305-5` gold *not_found*, predicted *partially_supported*
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
