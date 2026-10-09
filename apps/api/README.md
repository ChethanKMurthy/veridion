# Veridion API

The Python package `veridion`: HTTP API, background worker, document pipeline, assessment engine, requirement catalogues and database migrations. See the [repository README](../../README.md) for the product and [docs/architecture.md](../../docs/architecture.md) for the design.

## Develop

```bash
uv sync --extra postgres          # dependencies, including the PostgreSQL driver
uv run veridion serve --reload    # API on http://127.0.0.1:8000 with an embedded worker
uv run pytest                     # tests (SQLite, isolated per test)
uv run ruff check src tests migrations
```

Settings come from environment variables or `.env` files (the repository root, then this directory); see `.env.example`. Without `DATABASE_URL`, data lives in SQLite under `var/`, which is git-ignored.

## Command line

```
veridion serve [--host] [--port] [--reload] [--workers]   HTTP API
veridion worker                                          background jobs (stops cleanly on SIGTERM)
veridion db init | upgrade | downgrade | revision -m | check | current
veridion catalog validate | load                         requirement catalogues in catalog/
veridion samples generate                                fictional sample PDFs in samples/pdfs/
veridion seed demo [--mode rules|hybrid|auto] [--reset]  sample workspace
veridion demo snapshot                                   record the public demo into apps/web/public/demo
veridion eval run [--mode rules|hybrid|both] [--out]     evaluation suite
veridion admin set-plan --org <slug|id> --plan <plan>    change an organization's plan
```

## Layout

| Path | Contents |
|---|---|
| `src/veridion/api/` | Routers, auth and role dependencies, rate limits, serializers, error mapping |
| `src/veridion/pipeline/` | PDF parsing, OCR, tables, passages |
| `src/veridion/extraction/` | Metric, unit, number and period extraction |
| `src/veridion/retrieval/` | BM25 retrieval with explanations |
| `src/veridion/assessment/` | Rules, model assessment, merge policy, priorities, actions, diffs, engine |
| `src/veridion/benchmarking/` | Peer comparison |
| `src/veridion/llm/` | OpenAI-compatible provider with rate gate and cache |
| `src/veridion/jobs/` | Database-backed job queue and worker loop |
| `src/veridion/services/` | Documents, entitlements, usage, audit |
| `src/veridion/eval/` | Evaluation dataset and runner |
| `catalog/` | Versioned requirement catalogues (YAML) |
| `migrations/` | Alembic migrations |

## Changing the schema

Edit the models, then generate and review a migration:

```bash
uv run veridion db revision -m "describe the change"
uv run veridion db check        # fails if models and migrations disagree
```

Development databases are created directly from the models. If you later want to manage one with migrations, run `veridion db init` once to record it as current.

## Changing a catalogue

Catalogue versions are immutable once used by a run. To change requirements, copy the YAML to a new version, edit it, add a changelog entry, and run `veridion catalog validate`. The rules are explained in [docs/methodology.md](../../docs/methodology.md).
