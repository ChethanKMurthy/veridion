"""FastAPI application factory."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from veridion import __version__
from veridion.api import errors
from veridion.api.routes import assessments, auth, companies, documents, public, workspace
from veridion.config import get_settings

log = logging.getLogger("veridion")


def _configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from veridion.catalog import load_catalog
    from veridion.db import CATALOG_LOCK, create_all, lock_for_transaction, session_scope
    from veridion.jobs import EmbeddedWorker

    settings = get_settings()
    if not settings.is_production:
        create_all()  # production schemas are managed with Alembic (`veridion db upgrade`)
    elif not settings.cookie_secure:
        log.warning("COOKIE_SECURE is false: session cookies can travel over plain HTTP. "
                    "Set COOKIE_SECURE=true wherever the site is served over HTTPS.")
    try:
        with session_scope() as session:
            lock_for_transaction(session, CATALOG_LOCK)  # instances starting together load it once
            loaded = load_catalog(session)
            if loaded:
                log.info("Loaded requirement catalogues: %s", ", ".join(loaded))
    except Exception:
        log.exception("Requirement catalogue failed to load")
    worker = None
    if settings.embedded_worker:
        worker = EmbeddedWorker(settings.worker_poll_seconds)
        worker.start()
    app.state.worker = worker
    try:
        yield
    finally:
        if worker is not None:
            worker.shutdown()


def create_app() -> FastAPI:
    _configure_logging()
    settings = get_settings()
    app = FastAPI(
        title="Veridion API",
        version=__version__,
        description="Evidence-first company intelligence: documents, requirements, findings, peers and actions.",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Veridion-Client"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        started = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.url.path.startswith("/api/") and response.headers.get("content-type", "").startswith("application/json"):
            response.headers.setdefault("Cache-Control", "no-store")
        if elapsed > 1500:
            log.info("%s %s took %.0f ms (request %s)", request.method, request.url.path, elapsed, request_id)
        return response

    errors.install(app)
    for module in (public, auth, companies, documents, assessments, workspace):
        app.include_router(module.router, prefix="/api/v1")
    return app


app = create_app()
