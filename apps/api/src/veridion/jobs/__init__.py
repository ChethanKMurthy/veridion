"""A database-backed job queue.

Large uploads and assessment runs never block HTTP requests. Jobs are rows in
the `jobs` table; workers claim them with an optimistic conditional update
(plus `FOR UPDATE SKIP LOCKED` on PostgreSQL), so several worker processes can
run side by side. The queue can be swapped for Redis/SQS later without
changing handlers.
"""

from __future__ import annotations

import logging
import os
import socket
import threading
import time
import traceback
from collections.abc import Callable
from datetime import timedelta

from sqlalchemy import select, text, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from veridion.db import session_scope, utcnow
from veridion.models import Job

log = logging.getLogger("veridion.jobs")

STALE_AFTER = timedelta(minutes=30)

ProgressFn = Callable[[str, float, str], None]
Handler = Callable[[Session, Job, ProgressFn], dict]

_HANDLERS: dict[str, Handler] = {}


def handler(kind: str) -> Callable[[Handler], Handler]:
    def register(fn: Handler) -> Handler:
        _HANDLERS[kind] = fn
        return fn

    return register


def _load_handlers() -> None:
    if not _HANDLERS:
        from veridion.jobs import handlers  # noqa: F401  - registers handlers


def enqueue(session: Session, kind: str, payload: dict, org_id: str | None = None, max_attempts: int = 3) -> Job:
    job = Job(kind=kind, payload=payload, org_id=org_id, max_attempts=max_attempts,
              progress={"stage": "queued", "pct": 0, "message": "Waiting for a worker"})
    session.add(job)
    session.flush()
    return job


def _worker_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}:{threading.get_ident()}"


def claim_next(worker_id: str) -> str | None:
    """Atomically claim the oldest runnable job and return its id."""
    with session_scope() as session:
        now = utcnow()
        stmt = (
            select(Job.id)
            .where(Job.status == "queued", Job.run_after <= now)
            .order_by(Job.created_at)
            .limit(1)
        )
        if session.get_bind().dialect.name == "postgresql":
            stmt = stmt.with_for_update(skip_locked=True)
        job_id = session.execute(stmt).scalar_one_or_none()
        if job_id is None:
            return None
        claimed = session.execute(
            update(Job)
            .where(Job.id == job_id, Job.status == "queued")
            .values(status="running", locked_by=worker_id, locked_at=now, started_at=now,
                    attempts=Job.attempts + 1)
        )
        return job_id if claimed.rowcount == 1 else None


# Latest progress per job in this process. The API reads it first (embedded worker),
# falling back to the database row (separate worker processes).
LIVE_PROGRESS: dict[str, dict] = {}


def report_progress(job_id: str, stage: str, pct: float, message: str) -> None:
    """Best-effort progress: never blocks the job, even if the database is busy."""
    progress = {"stage": stage, "pct": round(max(0.0, min(100.0, pct)), 1), "message": message}
    LIVE_PROGRESS[job_id] = progress
    try:
        with session_scope() as session:
            sqlite = session.get_bind().dialect.name == "sqlite"
            if sqlite:
                session.execute(text("PRAGMA busy_timeout = 100"))
            try:
                session.execute(update(Job).where(Job.id == job_id).values(progress=progress))
            finally:
                if sqlite:
                    session.execute(text("PRAGMA busy_timeout = 30000"))
    except OperationalError:
        log.debug("Progress update for %s deferred (database busy)", job_id)


def run_job(job_id: str) -> None:
    _load_handlers()
    with session_scope() as session:
        job = session.get(Job, job_id)
        if job is None:
            return
        fn = _HANDLERS.get(job.kind)
        if fn is None:
            job.status, job.error, job.finished_at = "failed", f"No handler for job kind {job.kind!r}", utcnow()
            return

        kind = job.kind

    def progress(stage: str, pct: float, message: str) -> None:
        report_progress(job_id, stage, pct, message)

    started = time.perf_counter()
    log.info("Job %s (%s) started", job_id, kind)
    try:
        with session_scope() as session:
            job = session.get(Job, job_id)
            assert job is not None
            result = fn(session, job, progress) or {}
        with session_scope() as session:
            job = session.get(Job, job_id)
            assert job is not None
            job.status, job.result, job.finished_at, job.error = "succeeded", result, utcnow(), None
            job.progress = {"stage": "done", "pct": 100, "message": "Completed"}
        LIVE_PROGRESS.pop(job_id, None)
        log.info("Job %s (%s) succeeded in %.1f s", job_id, kind, time.perf_counter() - started)
    except Exception as exc:
        log.exception("Job %s (%s) failed after %.1f s", job_id, kind, time.perf_counter() - started)
        with session_scope() as session:
            job = session.get(Job, job_id)
            if job is None:
                return
            job.error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=8)}"
            if job.attempts < job.max_attempts and not isinstance(exc, PermanentJobError):
                job.status = "queued"
                job.run_after = utcnow() + timedelta(seconds=10 * 2 ** (job.attempts - 1))
                job.progress = {"stage": "retrying", "pct": 0, "message": f"Retrying after error: {exc}"}
            else:
                job.status, job.finished_at = "failed", utcnow()
                job.progress = {"stage": "failed", "pct": 100, "message": str(exc)[:500]}
            LIVE_PROGRESS.pop(job_id, None)
            on_failure = _FAILURE_HOOKS.get(job.kind)
            if on_failure and job.status == "failed":
                on_failure(session, job, exc)


class PermanentJobError(Exception):
    """An error that retrying cannot fix (corrupt file, missing record)."""


_FAILURE_HOOKS: dict[str, Callable[[Session, Job, Exception], None]] = {}


def on_failure(kind: str):
    def register(fn):
        _FAILURE_HOOKS[kind] = fn
        return fn

    return register


def requeue_stale() -> int:
    with session_scope() as session:
        result = session.execute(
            update(Job)
            .where(Job.status == "running", Job.locked_at < utcnow() - STALE_AFTER)
            .values(status="queued", locked_by=None, locked_at=None)
        )
        return result.rowcount or 0


def run_pending(limit: int = 100) -> int:
    """Process queued jobs synchronously (tests, CLI seeding)."""
    _load_handlers()
    count = 0
    worker = _worker_id()
    while count < limit:
        job_id = claim_next(worker)
        if job_id is None:
            break
        run_job(job_id)
        count += 1
    return count


def worker_loop(stop: threading.Event, poll_seconds: float = 1.0) -> None:
    _load_handlers()
    worker = _worker_id()
    log.info("Worker %s started", worker)
    requeue_stale()
    idle_ticks = 0
    while not stop.is_set():
        try:
            job_id = claim_next(worker)
        except Exception:
            log.exception("Failed to claim job")
            job_id = None
        if job_id:
            idle_ticks = 0
            run_job(job_id)
            continue
        idle_ticks += 1
        if idle_ticks % 300 == 0:
            requeue_stale()
        stop.wait(poll_seconds)
    log.info("Worker %s stopped", worker)


class EmbeddedWorker:
    """Runs the worker loop in a daemon thread inside the API process (development)."""

    def __init__(self, poll_seconds: float = 1.0) -> None:
        self.stop = threading.Event()
        self.thread = threading.Thread(
            target=worker_loop, args=(self.stop, poll_seconds), name="veridion-worker", daemon=True
        )

    def start(self) -> None:
        self.thread.start()

    def shutdown(self) -> None:
        self.stop.set()
        self.thread.join(timeout=10)
