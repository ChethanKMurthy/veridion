# Business plan (working draft)

**Status, October 2026:** working product, no customers, no revenue. Everything below about customers, pricing and the market is a hypothesis to test. Statements about the product are things it does today and can be checked in this repository.

## Summary

Sustainability consultants and reporting teams spend much of a reporting cycle reading long reports to find out which disclosure requirements are evidenced, which are missing, and where figures disagree. Veridion does the first pass: it reads a company's documents, checks them against a versioned requirement catalogue, links every finding to the passage that supports it, flags contradictions between documents, and turns gaps into a ranked action list. A person reviews and signs off; the software makes that review faster and auditable.

The first customer we intend to test is the **independent or boutique sustainability consultant serving mid-sized companies**: one buyer, many client workspaces, a recurring reporting calendar, and a painful manual process.

## The problem

For each client and reporting period, a consultant or reporting lead must:

1. Work out which requirements apply (and which version of each standard).
2. Find evidence for each requirement across sustainability reports, annual reports and supporting documents, often hundreds of pages.
3. Check the numbers: units, periods, boundaries, and whether two documents report the same figure differently.
4. Write up gaps and what to do about them, then do it all again next year or when the standard changes.

Steps 2 and 3 are slow, error-prone and hard to audit afterwards. Spreadsheets record conclusions but rarely the exact passage behind them. Inconsistent figures between a sustainability report and an annual report are easy to miss when they are expressed in different units (the demo's fictional example: 412,300 MWh in one report and 1,532,000 GJ in the other, a 3.2% difference).

## Why now

Requirement lists are changing, which forces re-mapping work:

- In June 2025 GRI published **GRI 102: Climate Change 2025** and **GRI 103: Energy 2025**, both effective **1 January 2027**. GRI 102 withdraws disclosures 305-1 to 305-5, and GRI 103 replaces GRI 302: Energy 2016 ([GRI 102](https://www.globalreporting.org/publications/documents/english/gri-102-climate-change-2025/), [GRI 103 FAQ](https://www.globalreporting.org/media/mead5ytn/gri-103-energy-2025-frequently-asked-questions-faqs.pdf), [Jones Day](https://trendingnowinesg.jonesday.com/post/102kqs7/gri-releases-new-climate-and-energy-standards-significant-reporting-changes-ahe)).
- On 3 July 2026 the European Commission adopted **revised ESRS**, with a substantial reduction in mandatory datapoints and a voluntary standard for undertakings outside the CSRD's scope. Advisers report application to financial years beginning on or after 1 January 2027, subject to the scrutiny period ([Cooley](https://www.cooley.com/news/insight/2026/2026-07-21-european-commission-adopts-revised-eu-csrd-reporting-standards), [EY](https://www.ey.com/en_gl/technical/csrd-technical-resources/eu-adopts-revised-esrs-for-sustainability-reporting), [Linklaters](https://sustainablefutures.linklaters.com/post/102n88h/eu-csrd-commission-adopts-revised-esrs-and-voluntary-reporting-standard), [PwC](https://viewpoint.pwc.com/gx/en/pwc/in-briefs/2026/ib_int202617.html)). Treat dates as provisional until publication in the Official Journal.

Every one of these changes invalidates a hard-coded checklist. Veridion stores requirements as versioned catalogues with effective dates and records which version each finding used, so re-mapping becomes a new run and a diff, not a new spreadsheet.

## What exists today

| Capability | State |
|---|---|
| PDF ingestion with OCR for scanned pages, table rows, running header removal | Working |
| Deterministic extraction of emissions, energy, water and waste values with unit and period normalisation | Working |
| Versioned requirement catalogues (GRI 302/305 2016 reviewed; GRI 102/103 2025 draft) | Working; narrow coverage |
| Five-status findings with cited passages, conflict detection, human-review routing | Working |
| Optional language-model review that can only cite supplied passages and cannot override conflicts | Working (Groq / any OpenAI-compatible provider) |
| Reviews, remediation actions ranked by importance × gap × urgency, run history and diffs | Working |
| Peer benchmarking with comparability notes | Working |
| Multi-tenant workspaces, roles, plan limits, usage metering, audit log | Working |
| Public demo on fictional companies, marketing site, trust and legal pages | Working |
| Billing, SSO, integrations, non-PDF inputs, non-English documents, other frameworks (ESRS, IFRS S2) | Not built |

Measured on the labelled evaluation set (small and developer-authored, so these describe controlled cases, not real-world accuracy): rules-only status accuracy 89.9% on all 139 cases; on a 45-case sample, gap-detection recall 100% for both modes and element recall 88.8% (rules) vs 96.6% (rules + model). See [evaluation.md](evaluation.md).

## Initial customer

Three candidate segments came out of the product brief. We start with one.

| Segment | Why | Why not first |
|---|---|---|
| **A. Sustainability and ESG consultants serving mid-sized companies** *(start here)* | One buyer, many client workspaces; recurring use each reporting cycle; evidence mapping is their billable but low-margin work | Small firms have tight budgets; must prove time saved |
| B. Investment research teams | Large budgets; comparison across companies | Needs broad, reliable financial data coverage we do not have |
| C. Reporting teams at mid-sized companies | Direct pain; simpler "readiness" need | One workspace each; slower to reach in volume |

**Buyer:** practice lead or partner at a consultancy of roughly 2–50 people. **Users:** their analysts. **Trigger:** a client's report is due, or a standard changes (GRI 102/103 from 2027).

**Not a fit (for now):** organisations looking for a full ESG data-management suite, an assurance opinion, or a tool that declares them compliant.

## Positioning

> Veridion maps a company's disclosures to requirements and shows the evidence for every finding.

What we say: every finding cites its source; contradictions are surfaced, not smoothed over; requirement versions are explicit; results are reproducible; AI is optional, bounded, and never the last word.

What we do not say: that Veridion determines compliance, replaces a consultant or an assurance provider, or covers frameworks it does not have catalogues for.

Customers' current alternatives are spreadsheets and manual reading, general-purpose AI assistants, and ESG reporting or data-management platforms. We do not claim those lack any particular feature; we compete on the reliability, traceability and speed of one specific workflow.

## Defensibility

Technology alone is not a moat. The advantages that can compound, and where each stands:

| Layer | Today | To build |
|---|---|---|
| Curated, versioned requirement catalogues with element-level checks | 2 framework sets, reviewed or labelled draft | Expert-reviewed catalogues for the frameworks our customers use, kept current |
| Labelled evaluation data | 139 developer-authored cases | Real, permissioned cases from design partners; publish accuracy per framework |
| Longitudinal company evidence | Versioned documents, metrics and run history per company | Coverage across periods and peers, with provenance |
| Workflow adoption | Reviews, actions, diffs, exports | Templates, evidence packages and approvals that teams rely on each cycle |

## Business model

Subscription per organization, priced by number of client companies (workspaces), documents and model-assisted runs. The product already enforces these limits through plans (`apps/api/src/veridion/services/entitlements.py`).

Pricing hypotheses from the product brief, **for customer interviews, not validated willingness to pay**:

| Tier | Offer | Illustrative price |
|---|---|---|
| Free / Explorer | One to three companies, limited documents, sample report | ₹0 |
| Individual | More documents, saved analyses and exports | ₹1,999–₹4,999 per month |
| Consultant / Professional | Multiple client workspaces, reusable evidence, comparison reports | ₹7,500–₹20,000 per month |
| Enterprise | Team controls, integrations, audit history, custom workflows | Custom |

Open decisions: the target geography and currency (the brief prices in INR; European consultants would expect EUR and a different price level), annual versus monthly billing, and whether model-assisted runs are metered separately. The website currently describes Explorer as free and Professional pilots as individually priced, which keeps options open during discovery.

## Unit economics

Variable costs are small; people's time is the real cost.

| Item | Measured or assumed | Figure |
|---|---|---|
| Rules-only assessment, 9 requirements | Measured (sample corpus) | ≈ 20 ms of compute |
| Document processing | Measured on 3–7 page samples | 0.2–0.5 s per document; real 100–300 page reports with scanned pages will take longer and should be measured |
| Model-assisted assessment, 9 requirements | Measured tokens: ≈ 15.7k input, ≈ 5.7k output | ≈ US$0.007 at Groq's published launch price for `openai/gpt-oss-120b` ($0.15 per million input tokens, $0.75 per million output tokens; [Groq](https://groq.com/blog/day-zero-support-for-openai-open-models)). Some trackers now list $0.60 for output; check current pricing |
| Model-assisted assessment, 100-requirement catalogue | Extrapolated | ≈ US$0.08; re-runs on unchanged inputs are served from cache |
| Hosting at pilot scale | Assumption | A fixed monthly cost (managed PostgreSQL, two small containers, object storage) that dominates variable cost until there are many customers; price it with your provider before setting plans |
| Catalogue curation | Assumption | Expert review of each new framework or version, and ongoing maintenance as standards change. This is the main recurring cost of goods |
| Onboarding and support | Assumption | Founder time per pilot; reduce with templates and documentation |

Implication: even the lowest paid price point covers the computing cost of heavy use many times over. Margins depend on keeping onboarding and catalogue work efficient, and on choosing frameworks that many customers share.

## Go-to-market

**Discovery (first)**, following the brief:

1. Find five sustainability or compliance consultants.
2. Ask how they collect evidence and prepare gap reports today, and how long it takes.
3. Request a typical workflow sample, with appropriately anonymised material.
4. Run it through Veridion and fix the most painful failure.
5. Show the output and measure time saved, errors caught, and how much manual checking remains.
6. Ask whether they would pay for continued access, and how much.

**Design partners (next):** two or three consultancies use Veridion on real (permissioned) client documents for one reporting cycle, free or at a nominal price, in exchange for feedback and permission to measure outcomes. Their documents, with consent, become the first real evaluation set.

**Acquisition channels to test:** practical writing on standard transitions (the site already has articles on GRI 102/103 and on evidence quality), the public demo as the call to action, sustainability-professional communities, and referrals from design partners. Founder-led sales throughout the pilot phase.

**Product gates for the pilot:** set `ALLOW_REGISTRATION=false` to run invite-only, keep `LLM_PROVIDER=none` for any partner who has not approved a model provider, and use the audit log and exports to show partners exactly what happened to their data.

## Metrics

| Stage | Metric |
|---|---|
| Value | Minutes from upload to first reviewed gap report; analyst time saved per report (measured with partners, not self-reported only) |
| Quality | Share of findings accepted without override; conflicts caught that the team had missed; evaluation accuracy per framework |
| Activation | Workspaces that complete a first run within 7 days of sign-up |
| Retention | Client companies assessed per organization per reporting cycle |
| Commercial | Pilot-to-paid conversion; price accepted versus the hypotheses above |

## Risks

| Risk | Mitigation |
|---|---|
| **The name.** "Veridion" is already used by an AI company-data platform for procurement, risk and compliance teams that also offers ESG data ([veridion.com](https://veridion.com/insights/articles/data-intelligence-platforms); formerly Soleadify, [renamed in 2023](https://tech.eu/2023/02/21/soleadify-is-now-veridion-with-6-million-further-to-its-name/)). The overlap in market makes confusion and a trademark dispute plausible. | Take legal advice and run a trademark search before any public launch, domain purchase or customer contract. Renaming is mechanical but broad: the name appears in about 130 files (copy, the Python package, cookie and header names). |
| Findings mistaken for compliance determinations | Product copy, terms and reports state the limits; human review is built into the workflow; accuracy is published with its caveats |
| Unknown accuracy on real reports | Evaluation so far is on fictional and synthetic documents; build a permissioned real-world set with design partners before making accuracy claims |
| Confidential client documents and AI | Rules-only mode sends nothing out; provider terms reviewed and listed as subprocessors; tenant isolation and audit log in place; security certifications later when customers require them |
| Standards churn | Versioned catalogues and run diffs; draft labelling for unreviewed sets; budget for curation |
| Larger platforms add similar features | Stay narrow on one customer type and one workflow; compete on measured quality and traceability |
| Model provider changes price or terms | OpenAI-compatible abstraction (any provider or a self-hosted model); rules-only fallback |

## Next 90 days

| Weeks | Goal | Done when |
|---|---|---|
| 1–2 | Decide the name and geography | Trademark advice received; currency and target region chosen |
| 1–4 | Discovery | Five consultant interviews written up; one workflow sample run through the product |
| 3–6 | Close the biggest gap the interviews reveal | Likely candidates: GRI 102/103 catalogue moved from draft to reviewed, larger-document performance, a client-ready export |
| 5–8 | Design partners | Two consultancies using Veridion on real client documents, invite-only |
| 6–10 | Real-world evaluation | A permissioned, labelled set from partner documents; accuracy published per requirement |
| 8–12 | First paid pilot | One signed pilot at a price that tests the hypotheses above |

## Sources

- GRI, [GRI Standards](https://www.globalreporting.org/standards/); [GRI 102: Climate Change 2025](https://www.globalreporting.org/publications/documents/english/gri-102-climate-change-2025/); [GRI 103: Energy 2025, FAQ](https://www.globalreporting.org/media/mead5ytn/gri-103-energy-2025-frequently-asked-questions-faqs.pdf)
- Jones Day, [GRI releases new climate and energy standards](https://trendingnowinesg.jonesday.com/post/102kqs7/gri-releases-new-climate-and-energy-standards-significant-reporting-changes-ahe)
- BDO, [GRI updates 2025–2027](https://www.bdo.ch/en-gb/insights/gri-updates-2025-2027-transparency-and-impact-in-sustainability)
- Cooley, [European Commission adopts revised EU CSRD reporting standards](https://www.cooley.com/news/insight/2026/2026-07-21-european-commission-adopts-revised-eu-csrd-reporting-standards)
- EY, [EU adopts revised ESRS for sustainability reporting](https://www.ey.com/en_gl/technical/csrd-technical-resources/eu-adopts-revised-esrs-for-sustainability-reporting)
- Grant Thornton, [European Commission adopts revised ESRS and voluntary standard](https://www.grantthornton.global/en/insights/articles/european-commission-adopts-revised-esrs-and-voluntary-standard/)
- Arendt, [Revised ESRS: Commission adopts delegated act](https://www.arendt.com/news-insights/news/revised-european-sustainability-reporting-standards-eu-commission-adopts-delegated-act/)
- Linklaters, [Commission adopts revised ESRS and voluntary reporting standard](https://sustainablefutures.linklaters.com/post/102n88h/eu-csrd-commission-adopts-revised-esrs-and-voluntary-reporting-standard)
- PwC, [In brief INT2026-17](https://viewpoint.pwc.com/gx/en/pwc/in-briefs/2026/ib_int202617.html)
- Groq, [Day zero support for OpenAI open models](https://groq.com/blog/day-zero-support-for-openai-open-models) (launch pricing)
- Veridion (veridion.com), [Data intelligence platforms](https://veridion.com/insights/articles/data-intelligence-platforms); tech.eu, [Soleadify is now Veridion](https://tech.eu/2023/02/21/soleadify-is-now-veridion-with-6-million-further-to-its-name/)
