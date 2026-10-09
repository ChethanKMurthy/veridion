# Changelog

All notable changes to Veridion are recorded here. Versions follow [Semantic Versioning](https://semver.org/); each release publishes container images to GitHub Container Registry.

## 0.1.0 (2026-10-09)

First release of the Veridion platform.

**Product**

- Evidence Explorer: five-status findings with weighted completeness, cited passages and a step-by-step evidence trail from requirement to source page to remediation.
- Cross-document contradiction detection after unit and period normalisation.
- Versioned requirement catalogues with effective dates: GRI 302 and GRI 305 (2016) reviewed; GRI 102 and GRI 103 (2025) as an early-adoption draft.
- Remediation actions ranked by importance × gap × urgency, persisted across runs and closed automatically when a gap is resolved.
- Peer benchmarking with comparability notes for period, boundary, method and unit.
- Immutable assessment runs with input manifests, run-to-run diffs with change attribution, and report, CSV and JSON exports.
- Public interactive demo on fictional companies, replaying recorded engine output.

**Engine**

- PDF pipeline with table rows as passages, Tesseract OCR for scanned pages, running header removal and deterministic evidence IDs.
- Deterministic extraction of emissions, energy, water and waste values with unit, scale-word and fiscal-period normalisation.
- Explainable BM25 retrieval; typed element checks; optional citation-bound, schema-validated model adjudication with a fixed merge policy.
- Labelled evaluation benchmark of 139 cases with published results.

**Platform**

- Multi-tenant organisations with five roles, scrypt password hashing, signed session cookies, CSRF protection and bearer tokens.
- Sign-in limits per address and per account; plan entitlements and usage metering; append-only audit log.
- PostgreSQL-backed job queue (`SKIP LOCKED`) with retries, stale-job recovery and graceful shutdown; advisory locks for migrations and catalogue loading.
- Alembic migrations with drift checks; Docker images, Docker Compose stack, Render Blueprint and Vercel configuration.
- Continuous integration covering API tests on PostgreSQL 17, the web build and a full container-stack smoke test.
