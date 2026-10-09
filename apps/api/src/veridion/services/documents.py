"""Document upload, versioning and processing."""

from __future__ import annotations

import re
import time
from datetime import date

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from veridion import EXTRACTION_VERSION, PIPELINE_VERSION
from veridion.config import get_settings
from veridion.db import utcnow
from veridion.extraction.periods import parse_period_label
from veridion.extraction.service import extract_for_passage
from veridion.ids import evidence_id, new_id, sha256_bytes
from veridion.jobs import PermanentJobError, enqueue, handler, on_failure
from veridion.models import Company, Document, ExtractedMetric, Job, Passage
from veridion.pipeline.pdf import PdfError, parse_pdf
from veridion.services import audit, entitlements, usage
from veridion.storage import get_storage


class UploadError(ValueError):
    pass


class DuplicateDocumentError(UploadError):
    """The same file is already a current document of this company."""

    def __init__(self, message: str, existing_id: str) -> None:
        super().__init__(message)
        self.existing_id = existing_id


_SAFE_NAME = re.compile(r"[^A-Za-z0-9._ -]+")


def _safe_filename(name: str) -> str:
    cleaned = _SAFE_NAME.sub("_", name).strip(" .") or "document.pdf"
    return cleaned[:200]


def create_document(session: Session, *, org_id: str, company: Company, data: bytes, filename: str,
                    title: str | None, doc_type: str, period_label: str | None, published_on: date | None,
                    uploaded_by: str | None, lineage_id: str | None = None, is_sample: bool = False,
                    source_url: str | None = None) -> tuple[Document, Job | None]:
    settings = get_settings()
    if not data.startswith(b"%PDF-"):
        raise UploadError("Only PDF files are supported.")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise UploadError(f"The file exceeds the {settings.max_upload_mb} MB upload limit.")
    entitlements.check_document_quota(session, org_id)

    period = None
    if period_label:
        period = parse_period_label(period_label, company.fiscal_year_end)
        if period is None:
            raise UploadError(f"Could not understand the reporting period {period_label!r}. Use e.g. FY2025.")

    version = 1
    previous: Document | None = None
    if lineage_id:
        previous = session.execute(
            select(Document).where(Document.org_id == org_id, Document.company_id == company.id,
                                   Document.lineage_id == lineage_id)
            .order_by(Document.version.desc()).limit(1)
        ).scalar_one_or_none()
        if previous is None:
            raise UploadError("The document being replaced was not found.")
        version = previous.version + 1

    digest = sha256_bytes(data)
    # The same file twice would duplicate every passage and inflate evidence counts.
    duplicate = session.execute(
        select(Document).where(Document.org_id == org_id, Document.company_id == company.id,
                               Document.sha256 == digest, Document.superseded_at.is_(None))
    ).scalars().first()
    if duplicate is not None:
        storage = get_storage()
        if storage.exists(duplicate.storage_key):
            raise DuplicateDocumentError(
                f"This file is already uploaded as “{duplicate.title}” (version {duplicate.version}).", duplicate.id)
        # The stored copy was lost (hosts without persistent disks): uploading the same file restores it.
        storage.put(duplicate.storage_key, data, "application/pdf")
        return duplicate, None

    doc_id = new_id("doc")
    key = f"orgs/{org_id}/companies/{company.id}/documents/{doc_id}/{digest[:16]}.pdf"
    get_storage().put(key, data, "application/pdf")

    doc = Document(
        id=doc_id, org_id=org_id, company_id=company.id, lineage_id=lineage_id or doc_id, version=version,
        title=(title or (previous.title if previous else None) or _safe_filename(filename).rsplit(".", 1)[0])[:300],
        doc_type=doc_type, filename=_safe_filename(filename), storage_key=key, sha256=digest, size_bytes=len(data),
        period_label=period.label if period else (previous.period_label if previous else None),
        period_start=period.start if period else (previous.period_start if previous else None),
        period_end=period.end if period else (previous.period_end if previous else None),
        published_on=published_on, source_url=source_url, uploaded_by=uploaded_by, is_sample=is_sample,
    )
    session.add(doc)
    if previous is not None:
        previous.superseded_at = utcnow()
        previous.superseded_by = doc_id
    session.flush()
    job = enqueue(session, "process_document", {"document_id": doc.id}, org_id=org_id)
    audit.record(session, org_id=org_id, actor_id=uploaded_by, action="document.uploaded", entity_type="document",
                 entity_id=doc.id, data={"filename": doc.filename, "sha256": digest, "version": version,
                                         "replaces": previous.id if previous else None})
    return doc, job


def current_documents(session: Session, org_id: str, company_id: str) -> list[Document]:
    return list(session.execute(
        select(Document).where(Document.org_id == org_id, Document.company_id == company_id,
                               Document.superseded_at.is_(None))
        .order_by(Document.created_at)
    ).scalars())


@handler("process_document")
def process_document_job(session: Session, job: Job, progress) -> dict:
    doc = session.get(Document, job.payload["document_id"])
    if doc is None:
        raise PermanentJobError("Document no longer exists.")
    return process_document(session, doc, progress)


@on_failure("process_document")
def _mark_failed(session: Session, job: Job, exc: Exception) -> None:
    doc = session.get(Document, job.payload.get("document_id"))
    if doc is not None:
        doc.status = "failed"
        doc.error = str(exc)[:1000]


def process_document(session: Session, doc: Document, progress=None) -> dict:
    progress = progress or (lambda *_: None)
    company = session.get(Company, doc.company_id)
    assert company is not None
    doc.status, doc.error = "processing", None
    session.commit()  # release locks while parsing; the final write happens in one transaction
    progress("parsing", 10, "Extracting text, tables and page references")

    started = time.perf_counter()
    data = get_storage().get(doc.storage_key)
    settings = get_settings()
    try:
        parsed = parse_pdf(data, fiscal_year_end=company.fiscal_year_end, period_hint=doc.period_label,
                           ocr_enabled=settings.ocr_enabled)
    except PdfError as exc:
        raise PermanentJobError(str(exc)) from exc
    entitlements.check_page_limit(session, doc.org_id, parsed.page_count)

    progress("indexing", 55, f"Indexing {len(parsed.passages)} passages")
    session.execute(delete(ExtractedMetric).where(ExtractedMetric.document_id == doc.id))
    session.execute(delete(Passage).where(Passage.document_id == doc.id))
    session.flush()

    default_period = parsed.detected_period
    seen_ids: set[str] = set()
    stored: list[tuple[str, object]] = []
    for ordinal, p in enumerate(parsed.passages):
        pid = evidence_id(doc.id, p.page, ordinal, p.text)
        if pid in seen_ids:
            continue
        seen_ids.add(pid)
        stored.append((pid, p))
        session.add(Passage(
            id=pid, org_id=doc.org_id, company_id=doc.company_id, document_id=doc.id, page=p.page, ordinal=ordinal,
            kind=p.kind, section=(p.section or None) and p.section[:300], text=p.text, bbox=list(p.bbox),
            extraction_method=p.method, confidence=p.confidence, table_ref=p.table_ref, cells=p.cells,
        ))
    session.flush()  # passages must exist before metrics reference them

    metric_count = 0
    for pid, p in stored:
        seen_values: set[tuple] = set()
        for value in extract_for_passage(p.kind, p.text, p.section, p.cells, p.confidence, default_period,
                                         company.fiscal_year_end):
            signature = (value.metric_key, round(value.value, 6), value.unit, value.period_label)
            if signature in seen_values:
                continue
            seen_values.add(signature)
            session.add(ExtractedMetric(
                org_id=doc.org_id, company_id=doc.company_id, document_id=doc.id, passage_id=pid,
                metric_key=value.metric_key, label=value.label, value=value.value, unit=value.unit,
                normalized_value=value.normalized_value, normalized_unit=value.normalized_unit,
                period_label=value.period_label, period_start=value.period_start, period_end=value.period_end,
                qualifiers=value.qualifiers, confidence=value.confidence, method=value.method,
                raw_text=value.raw_text,
            ))
            metric_count += 1
    progress("finalising", 90, "Recording document metadata")

    doc.page_count = parsed.page_count
    doc.page_sizes = [list(s) for s in parsed.page_sizes]
    if parsed.detected_period and not doc.period_label:
        doc.period_label = parsed.detected_period.label
        doc.period_start = parsed.detected_period.start
        doc.period_end = parsed.detected_period.end
    doc.ocr_pages = parsed.ocr_pages
    doc.processing_stats = {
        **parsed.stats, "metrics": metric_count, "warnings": parsed.warnings,
        "total_ms": round((time.perf_counter() - started) * 1000, 1),
        "detected_title": parsed.title,
    }
    doc.pipeline_version, doc.extraction_version = PIPELINE_VERSION, EXTRACTION_VERSION
    doc.status, doc.processed_at = "ready", utcnow()
    usage.record(session, doc.org_id, "pages_processed", parsed.page_count, ref_id=doc.id)
    usage.record(session, doc.org_id, "documents_processed", 1, ref_id=doc.id)
    return {"passages": len(seen_ids), "metrics": metric_count, "pages": parsed.page_count,
            "ocr_pages": parsed.ocr_pages}


def document_count(session: Session, org_id: str) -> int:
    return session.execute(
        select(func.count()).select_from(Document).where(Document.org_id == org_id, Document.superseded_at.is_(None))
    ).scalar_one()
