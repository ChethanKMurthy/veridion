# Deployment and operations

Veridion ships as two container images and needs a PostgreSQL database and somewhere to keep files. This guide covers a single-machine deployment with Docker Compose, the move to managed services, configuration, scaling and day-to-day operations. For how the pieces fit together see [architecture.md](architecture.md).

## What you deploy

| Unit | Image | Command | Instances |
|---|---|---|---|
| Web | `apps/web/Dockerfile` (Next.js standalone server) | `node server.js` | 1+ (stateless) |
| API | `apps/api/Dockerfile` | `veridion serve --host 0.0.0.0` | 1+ (stateless) |
| Worker | same API image | `veridion worker` | 1+ (stateless) |
| Migrations | same API image | `veridion db upgrade` (or `veridion serve --migrate` where there is no release step) | once per release, before new API instances start |
| Database | PostgreSQL 16 or 17 | — | 1 (managed in production) |
| Files | local volume, or any S3-compatible bucket | — | — |

The web server proxies `/api/*` to the API, so browsers see a single origin and the session cookie stays first-party. Next.js compiles that rewrite at build time: build the web image with `--build-arg VERIDION_API_URL=<the API's address as the web server reaches it>`.

## Single machine with Docker Compose

`docker-compose.yml` runs the whole stack in production mode: PostgreSQL, a one-shot migration, the API with two server processes, a worker and the web app.

```bash
cp .env.example .env
# Set at least:
#   SECRET_KEY=<python -c "import secrets; print(secrets.token_urlsafe(48))">
#   POSTGRES_PASSWORD=<a strong password>
docker compose up --build --detach
docker compose run --rm api veridion seed demo --mode rules   # optional sample workspace
```

Open http://localhost:3000. Sign in to the sample workspace as `demo@veridion.example` / `veridion-demo`, or create a workspace at `/sign-up`.

To serve it publicly from one VM, put a TLS-terminating proxy in front of port 3000 and set `COOKIE_SECURE=true` and `SITE_URL=https://your-domain`. With Caddy:

```
your-domain.example {
    reverse_proxy localhost:3000
}
```

Uploaded documents live in the `storage` volume and the database in `postgres-data`; back both up (see [Backups](#backups)).

## Managed services

When one machine is no longer enough, or you want managed backups, move each unit to a managed equivalent. Nothing in the code is tied to a particular provider.

| Unit | Options |
|---|---|
| Database | Any managed PostgreSQL (AWS RDS, Google Cloud SQL, Azure Database, Neon, Supabase). Use the `postgresql+psycopg://` URL scheme. |
| Files | Any S3-compatible store (AWS S3, Cloudflare R2, Google Cloud Storage via its S3 interface, MinIO). Keep the bucket private; the API serves files to authorised users. |
| API and worker | Any container platform (AWS ECS/Fargate, Google Cloud Run, Azure Container Apps, Fly.io, Render, Railway, Kubernetes). Run migrations as a release or pre-deploy step. Workers need no inbound traffic. |
| Web | The same container platform, or Vercel. On Vercel, set `VERIDION_API_URL` to the API's public HTTPS URL in the project's environment so the rewrite targets it at build time. |

Two settings matter when components move apart:

- **`FORWARDED_ALLOW_IPS`** on the API lists the proxies whose `X-Forwarded-For` header is trusted (IPs or CIDR ranges). Include the load balancer and the web servers' network, and nothing else. If the web tier's egress addresses cannot be listed, per-address rate limits apply to the proxy's address; per-account sign-in limits still apply.
- **The public entry point should overwrite or append `X-Forwarded-For`.** Next.js forwards a client-supplied header unchanged when it is the first hop, so put a load balancer or reverse proxy in front of the web tier in production.

## Vercel and Render

The repository includes `render.yaml`, a Render Blueprint for the API (Docker, Singapore region) and its PostgreSQL database. The web app deploys to Vercel and proxies `/api/*` to Render, so browsers only ever talk to the Vercel domain.

**1. API and database on Render.** In the Render dashboard choose **New → Blueprint** and select this repository (or open `https://render.com/deploy?repo=<repository URL>`). Render prompts for:

- `GROQ_API_KEY`: a Groq key for rules + model assessments; leave it empty for rules only.
- `PLATFORM_ADMIN_EMAILS`: your email, to read website enquiries and change plans through the API.

It then creates `veridion-db` and `veridion-api`. The API applies migrations when it starts and loads the requirement catalogues. Check `https://<api host>/api/v1/ready`.

**2. Web on Vercel.** Import the repository with **Root Directory `apps/web`** (framework Next.js) and set, for Production:

| Variable | Value |
|---|---|
| `VERIDION_API_URL` | The API service's Render URL, `https://<service>.onrender.com` |
| `NEXT_PUBLIC_SITE_URL` | Optional: a custom domain. Without it the Vercel production domain (here `https://veridion-nine.vercel.app`) is used. |

Rewrites are compiled at build time, so redeploy the web app after changing `VERIDION_API_URL`. From the command line: `cd apps/web && vercel link`, add the two variables with `vercel env add`, then `vercel deploy --prod`.

**Free plan trade-offs** (the Blueprint's default):

- The API sleeps after 15 minutes without traffic; the first request after that waits about a minute. The marketing site and `/demo` are static on Vercel and unaffected.
- Uploaded PDFs live on the instance's disk, which is wiped when the API restarts or sleeps. Findings and passages survive in the database, but page images and downloads of earlier uploads stop working. Use S3-compatible storage (set `STORAGE_BACKEND=s3` and the `S3_*` variables, for example Cloudflare R2) or a paid instance with a disk.
- The free database is deleted 30 days after creation (with a 14-day grace period to upgrade) and has no backups.
- Jobs run inside the API process (`EMBEDDED_WORKER=true`), because free plans have no background workers.

**Moving to paid plans:** change `plan: free` to a paid instance type in `render.yaml`, add a `disk:` (for example `mountPath: /app/var/storage`, `sizeGB: 1`) or S3 settings, upgrade the database plan, and optionally add a `type: worker` service running `veridion worker` with `EMBEDDED_WORKER=false` on the API.

## Configuration

All settings are environment variables (or entries in a `.env` file next to the API). `.env.example` lists every one with its default.

| Variable | Default | Notes |
|---|---|---|
| `VERIDION_ENV` | `development` | `production` disables table auto-creation and requires `SECRET_KEY`. The images set it. |
| `SECRET_KEY` | — | **Required in production.** Signs session tokens. Rotating it signs everyone out. |
| `DATABASE_URL` | SQLite in `apps/api/var/` | `postgresql+psycopg://user:password@host:5432/db` in production. |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` | 5, 10 | Connections per process. See [Scaling](#scaling). |
| `COOKIE_SECURE` | `false` | Set `true` whenever the site is served over HTTPS. Production logs a warning when it is false. |
| `CORS_ORIGINS` | `http://localhost:3000` | Only needed for browsers calling the API directly; the web proxy does not need it. |
| `ALLOW_REGISTRATION` | `true` | `false` closes self-service sign-up (invite-only pilots). |
| `PLATFORM_ADMIN_EMAILS` | — | Comma-separated operator emails that may read website enquiries and change plans through the API. |
| `WEB_CONCURRENCY` | 1 | API server processes. |
| `FORWARDED_ALLOW_IPS` | `127.0.0.1,::1` | Trusted proxies for client addresses. |
| `EMBEDDED_WORKER` | `true` | Runs a worker thread inside the API. The images set it to `false`; run `veridion worker` instead. |
| `STORAGE_BACKEND` | `local` | `local` or `s3`. |
| `STORAGE_DIR` | `apps/api/var/storage` | For `local`. Must be shared by API and workers. |
| `S3_BUCKET`, `S3_ENDPOINT_URL`, `S3_REGION`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` | — | For `s3`. Leave the endpoint empty for AWS. |
| `MAX_UPLOAD_MB` | 50 | Per-file upload limit. |
| `OCR_ENABLED` | `true` | Requires the `tesseract` binary (installed in the API image). |
| `LLM_PROVIDER` | `none` | `groq`, `openai_compatible` or `none` (rules only). |
| `GROQ_API_KEY` | — | For `groq`. |
| `LLM_BASE_URL`, `LLM_API_KEY` | — | For `openai_compatible` (for example a self-hosted model server). |
| `LLM_MODEL` | `openai/gpt-oss-120b` | Must support JSON-schema structured output for best results. |
| `LLM_MAX_CONCURRENCY` | 2 | Parallel model calls per assessment. |
| `LLM_TIMEOUT_SECONDS` | 60 | Per call; calls are retried with backoff and fall back to rules on failure. |
| `VERIDION_API_URL` | `http://127.0.0.1:8000` | Web build argument: where `/api/*` is proxied. |
| `NEXT_PUBLIC_SITE_URL` | `http://localhost:3000` | Web build argument: canonical URL for metadata. |

### Model provider and data handling

In *rules + model* mode, excerpts of the customer's documents (up to 12 passages of at most 600 characters per requirement) are sent to the configured provider. Before enabling it for customer data, confirm the provider's data retention and training terms, record it as a subprocessor (the website's `/trust/subprocessors` page lists the current ones), and offer customers a rules-only option. Rules-only mode sends nothing outside your infrastructure. Plans cap the number of model-assisted runs per month.

## Releases

Versions follow semantic versioning and are recorded in `CHANGELOG.md`. To cut a release, add a section for the new version to the changelog, then push a tag:

```bash
git tag -a v0.2.0 -m "Veridion 0.2.0"
git push origin v0.2.0
```

The release workflow (`.github/workflows/release.yml`) builds both images for `linux/amd64` and `linux/arm64`, publishes them to GitHub Container Registry as `ghcr.io/<owner>/veridion-api` and `ghcr.io/<owner>/veridion-web` (tags `0.2.0`, `0.2`, `latest` and `sha-<commit>`) with SBOM and provenance attestations, and creates a GitHub Release with the changelog section and the OpenAPI specification attached. The published web image proxies `/api/*` to `http://api:8000`, which matches the Compose stack; other topologies build the web image with their own `VERIDION_API_URL`.

To run the Compose stack on published images instead of local builds:

```bash
VERIDION_API_IMAGE=ghcr.io/<owner>/veridion-api:0.2.0 \
VERIDION_WEB_IMAGE=ghcr.io/<owner>/veridion-web:0.2.0 \
docker compose up --no-build --detach
```

Rolling out a release:

1. Use the release's images (or build both from the tagged commit). CI (`.github/workflows/ci.yml`) has already built and smoke-tested them.
2. Run `veridion db upgrade` with the new API image against the production database. Write migrations so they can be applied while the previous release is still running: add columns and tables first, and remove old ones in a later release.
3. Roll the workers, then the API, then the web tier. Workers finish their current job on `SIGTERM` (give them a two-minute grace period).

Create a migration after changing models with `uv run veridion db revision -m "describe the change"`, review the generated file, and commit it. `make db-check` (and CI) fail if models and migrations disagree.

## Scaling

| Pressure | Lever |
|---|---|
| API latency under load | More API processes (`WEB_CONCURRENCY`) or instances. The API is stateless apart from in-process rate-limit counters. |
| Queue backlog (documents waiting, runs slow to start) | More workers. Jobs are claimed with `SKIP LOCKED`, so workers never take the same job. |
| Model rate limits | Raise the provider tier, lower `LLM_MAX_CONCURRENCY`, or run more assessments in rules-only mode. Cached responses are reused across runs. |
| Database connections | Each process may open `DB_POOL_SIZE + DB_MAX_OVERFLOW` connections. Keep (API processes + workers) × that total below PostgreSQL's `max_connections` (100 by default), or put PgBouncer in front. |
| Several API instances | Move rate limiting to a shared store such as Redis so limits apply across instances. |

## Health and monitoring

| Signal | Where |
|---|---|
| Liveness | `GET /api/v1/health`: the process is up |
| Readiness | `GET /api/v1/ready`: the database answers |
| Request tracing | Every API response has an `X-Request-ID`; pass your own to correlate with upstream logs |
| Logs | stdout from every container; workers log each job's start, outcome and duration |
| Jobs | `GET /api/v1/jobs/{id}` for one job; failed jobs keep their error message |
| Security events | The `audit_events` table: sign-ins, failed sign-ins, membership, role and plan changes, uploads, deletions, assessments, exports |

Alert on readiness failures, a growing count of queued jobs older than a few minutes, and repeated failed jobs.

## Backups

- **Database:** use your provider's automated backups with point-in-time recovery, or `pg_dump` on a schedule for Compose deployments.
- **Files:** enable versioning on the bucket, or snapshot the `storage` volume. The database records each file's storage key and SHA-256, so restore the database and the files from the same point in time.
- Test a restore before you need one.

## Operator commands

```bash
veridion db upgrade                      # apply migrations
veridion db check                        # models and migrations agree
veridion catalog validate                # check requirement catalogue files
veridion catalog load                    # load new catalogue versions (the API also does this at startup)
veridion admin set-plan --org <slug-or-id> --plan professional
veridion seed demo --mode rules          # (re)create the sample workspace
veridion demo snapshot                   # re-record the public /demo from the sample workspace
veridion eval run --mode rules           # run the evaluation suite
```

Inside Compose, prefix with `docker compose run --rm api`.

## Production checklist

- [ ] `SECRET_KEY` is long, random and stored in a secret manager
- [ ] `COOKIE_SECURE=true` and the site is served only over HTTPS
- [ ] `POSTGRES_PASSWORD` (or the managed database credentials) changed from defaults
- [ ] `FORWARDED_ALLOW_IPS` lists only your proxies; a load balancer sets `X-Forwarded-For`
- [ ] Object storage bucket is private, versioned and backed up
- [ ] Database backups are automated and a restore has been tested
- [ ] Model provider terms reviewed and the provider listed as a subprocessor (or `LLM_PROVIDER=none`)
- [ ] `ALLOW_REGISTRATION` set to match how you onboard customers
- [ ] `PLATFORM_ADMIN_EMAILS` limited to operators
- [ ] Alerts on readiness, queue age and failed jobs
- [ ] The sample workspace is not seeded in production unless you intend to show it
