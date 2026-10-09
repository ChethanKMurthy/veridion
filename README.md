# Veridion

Evidence-first company intelligence. Veridion reads a company's sustainability and annual reports, checks them against versioned disclosure requirements, and links every finding to the exact passage that supports it, so gaps, contradictions and next actions can be verified rather than taken on trust.

> **Status:** working product in its pilot phase, with no customers yet. The demo uses fictional companies. The name "Veridion" is already used by another company in a related market; see [Risks](docs/business-plan.md#risks) before launching publicly under it.

## What it does

- **Reads documents properly.** PDFs, including scanned pages (OCR), tables split into rows, running headers removed, every passage addressable by a stable ID.
- **Extracts the numbers.** Emissions, energy, water and waste values, with units normalised (tCO2e, MWh, m³, t) and periods aligned to the company's fiscal year.
- **Assesses each requirement.** Supported, partially supported, not found, conflicting or needs review, with weighted completeness and the passages that justify it.
- **Catches contradictions.** The same metric reported differently across documents (after unit conversion) is flagged and never smoothed over.
- **Uses AI with limits.** An optional language model reviews each requirement. It can cite only passages Veridion found and cannot override detected conflicts; disagreements go to a person.
- **Turns gaps into work.** Actions ranked by importance × gap × urgency, owners and due dates, closed automatically when a later run no longer shows the gap.
- **Compares peers honestly.** Benchmarks show period, boundary, method and unit caveats; "not disclosed" is never shown as zero.
- **Keeps a record.** Every run stores its documents' hashes, catalogue version and engine versions; any two runs can be compared, and changes are attributed to their cause.

## Try it

**Public demo:** start the web app and open `/demo`. It runs the real workspace screens on recorded engine output for three fictional companies, with a guided scenario.

**Local workspace** (sign in as `demo@veridion.example` / `veridion-demo` after seeding):

```bash
# Prerequisites: Python 3.12 with uv, Node.js 22+, and optionally Tesseract for scanned PDFs
cp .env.example .env          # LLM_PROVIDER=none runs rules only; set GROQ_API_KEY for rules + model
make setup                    # install API and web dependencies
make seed MODE=rules          # create the sample workspace (MODE=hybrid uses the model)
make dev                      # API on :8000 with an embedded worker, web on :3000
```

Open http://localhost:3000. API documentation is at http://localhost:3000/api/docs.

**Hosted:** the web app deploys to Vercel and the API and database to Render using the included `render.yaml`; see [Vercel and Render](docs/deployment.md#vercel-and-render).

**Production-shaped stack** (PostgreSQL, migrations, API, worker, web) with Docker:

```bash
# In .env: SECRET_KEY=<python -c "import secrets; print(secrets.token_urlsafe(48))"> and POSTGRES_PASSWORD=<...>
docker compose up --build --detach
docker compose run --rm api veridion seed demo --mode rules
```

## How it is built

```
Browser ──▶ Next.js web (marketing site, /demo, /app) ──/api/*──▶ FastAPI ──▶ PostgreSQL
                                                                     │            ▲
                                                               object storage     │ jobs (SKIP LOCKED)
                                                                     ▲            │
                                                                     └── worker ──┴──▶ LLM provider (optional)
```

| Part | Stack |
|---|---|
| Web | Next.js 16 (App Router, Cache Components), React 19, Tailwind CSS 4, SWR |
| API and worker | Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PyMuPDF, Tesseract |
| Data | PostgreSQL (SQLite for development and tests), local disk or S3-compatible storage |
| Model | Any OpenAI-compatible endpoint; Groq `openai/gpt-oss-120b` by default; optional |

The API, worker and migrations share one image; everything is stateless apart from the database and object storage, so each tier scales horizontally. Details: [architecture](docs/architecture.md).

## Quality

Measured on a labelled evaluation set of 139 cases (27 hand-labelled on the sample corpus, 112 synthetic). The set is small and written by the developers, so it shows behaviour on controlled cases, not accuracy on real-world reports.

| Metric | Rules only (139 cases) | Rules + model (45-case sample) |
|---|---|---|
| Status accuracy, five classes | 89.9% | 93.3% |
| Gap detection recall | 97.1% | 100% |
| Contradiction detection, precision and recall | 100% / 100% | 100% / 100% |
| Citation validity | 100% | 100% |
| Numeric extraction accuracy | 96.5% | 100% |

Full results, including failures: [evaluation.md](docs/evaluation.md) and [evaluation-rules-full.md](docs/evaluation-rules-full.md). Reproduce with `make eval`.

Engineering checks: 66 API tests (`make test`), Ruff and ESLint (`make lint`), TypeScript (`make typecheck`), and a migration drift check (`make db-check`). CI runs all of these, applies migrations and seeds the sample workspace on PostgreSQL, then builds both container images and smoke-tests the full stack.

## Repository

```
apps/api/        Python package `veridion`: API, worker, pipeline, assessment engine, catalogues, migrations, tests
apps/web/        Next.js site, public demo and workspace
docs/            Architecture, methodology, deployment, evaluation, business plan
docker-compose.yml, Makefile, .github/workflows/ci.yml
PRODUCT.md, DESIGN.md   Product principles and the design system
```

`make help` lists every command.

## Documentation

| Document | For |
|---|---|
| [Methodology](docs/methodology.md) | How findings are produced: statuses, checks, conflicts, the model merge policy, priorities |
| [Architecture](docs/architecture.md) | Components, data model, security model, scaling path |
| [Deployment](docs/deployment.md) | Docker, managed services, configuration, releases, monitoring, backups |
| [Evaluation](docs/evaluation.md) | Accuracy on the labelled set, rules vs rules + model |
| [Business plan](docs/business-plan.md) | Initial customer, positioning, pricing hypotheses, unit economics, risks, next 90 days |
| [Product](PRODUCT.md) and [design](DESIGN.md) | Principles, tone and the visual system |

## Limitations

- Requirement coverage is narrow: GRI 302/305 (2016) reviewed, GRI 102/103 (2025) as a draft. Other frameworks need catalogues and expert review.
- Inputs are English-language PDFs. Spreadsheets and other languages are not supported yet.
- Accuracy has been measured on fictional and synthetic documents only.
- No billing, SSO or third-party integrations yet.
- Rate limits are per API process; use a shared store when running several API instances.

## Roadmap

1. Customer discovery with sustainability consultants, then design partners on real (permissioned) documents.
2. GRI 102/103 catalogue from draft to reviewed; a real-world evaluation set.
3. Client-ready report exports and evidence packages; larger-document performance.
4. Additional frameworks as customers require them (for example revised ESRS), billing, SSO.

## License

Proprietary. All rights reserved.
