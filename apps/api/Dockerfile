# syntax=docker/dockerfile:1
#
# Veridion API and worker image. The same image runs three roles:
#   veridion serve --host 0.0.0.0     HTTP API (add --migrate where there is no release step)
#   veridion worker                   background jobs (document processing, assessments)
#   veridion db upgrade               schema migrations (run once per release)
#
# The project is installed in editable mode under /app (mirroring apps/api), because the
# application locates its catalogue, migrations and sample documents relative to its source.

FROM python:3.12-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /app

# Dependencies first, so editing the source does not invalidate this layer.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project --extra postgres --extra s3

COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --extra postgres --extra s3


FROM python:3.12-slim-bookworm AS runtime

# Tesseract reads scanned pages; English language data is installed with it.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 10001 veridion \
    && useradd --system --uid 10001 --gid veridion --home-dir /app --shell /usr/sbin/nologin veridion

WORKDIR /app
COPY --from=build /app /app
COPY alembic.ini ./
COPY migrations ./migrations
COPY catalog ./catalog
COPY samples ./samples
RUN mkdir -p /app/var/storage && chown -R veridion:veridion /app/var

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VERIDION_ENV=production \
    EMBEDDED_WORKER=false \
    PORT=8000

USER veridion
EXPOSE 8000
# Listens on $PORT (hosting platforms such as Render set it; 8000 otherwise).
CMD ["veridion", "serve", "--host", "0.0.0.0"]
