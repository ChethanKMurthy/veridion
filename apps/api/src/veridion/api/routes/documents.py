"""Document upload, versions, files, rendered pages, passages and search."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from veridion.api import serializers as S
from veridion.api.deps import WRITE_ROLES, Principal, get_principal, require_roles
from veridion.api.routes.companies import evidence_usage
from veridion.assessment.context import short_doc_name
from veridion.config import get_settings
from veridion.db import get_db
from veridion.jobs import enqueue
from veridion.models import Document, ExtractedMetric, Finding, FindingEvidence, Job, Passage
from veridion.models.documents import DOC_TYPES
from veridion.pipeline.pdf import PdfError, render_page_png
from veridion.retrieval import BM25Index, Doc
from veridion.services import audit
from veridion.services.documents import create_document, current_documents
from veridion.storage import get_storage

router = APIRouter(tags=["documents"])


def _latest_job(db: Session, doc: Document) -> Job | None:
    rows = db.execute(select(Job).where(Job.kind == "process_document", Job.org_id == doc.org_id)
                      .order_by(Job.created_at.desc()).limit(50)).scalars()
    return next((j for j in rows if j.payload.get("document_id") == doc.id), None)


@router.get("/companies/{company_id}/documents")
def list_documents(company_id: str, include_superseded: bool = False, principal: Principal = Depends(get_principal),
                   db: Session = Depends(get_db)) -> list[dict]:
    c = S.company_or_404(db, principal.org_id, company_id)
    if include_superseded:
        docs = db.execute(select(Document).where(Document.org_id == principal.org_id, Document.company_id == c.id)
                          .order_by(Document.created_at)).scalars().all()
    else:
        docs = current_documents(db, principal.org_id, c.id)
    return [S.document(d, job_row=_latest_job(db, d) if d.status in ("uploaded", "processing", "failed") else None)
            for d in docs]


@router.post("/companies/{company_id}/documents", status_code=201)
async def upload_document(
    company_id: str,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    doc_type: str = Form(default="other"),
    period_label: str | None = Form(default=None),
    published_on: date | None = Form(default=None),
    source_url: str | None = Form(default=None),
    replaces: str | None = Form(default=None),
    principal: Principal = Depends(require_roles(*WRITE_ROLES)),
    db: Session = Depends(get_db),
) -> dict:
    c = S.company_or_404(db, principal.org_id, company_id)
    if doc_type not in DOC_TYPES:
        raise HTTPException(422, f"doc_type must be one of {', '.join(DOC_TYPES)}")
    limit = get_settings().max_upload_mb * 1024 * 1024
    data = await file.read(limit + 1)
    lineage_id = None
    if replaces:
        prior = S.document_or_404(db, principal.org_id, replaces)
        if prior.company_id != c.id:
            raise HTTPException(400, "The replaced document belongs to another company.")
        lineage_id = prior.lineage_id
    doc, job = create_document(
        db, org_id=principal.org_id, company=c, data=data, filename=file.filename or "document.pdf", title=title,
        doc_type=doc_type, period_label=period_label or None, published_on=published_on,
        uploaded_by=principal.user_id, lineage_id=lineage_id, source_url=source_url,
    )
    return S.document(doc, job_row=job)


@router.get("/documents/{document_id}")
def get_document(document_id: str, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> dict:
    doc = S.document_or_404(db, principal.org_id, document_id)
    versions = db.execute(select(Document).where(Document.org_id == principal.org_id,
                                                 Document.lineage_id == doc.lineage_id)
                          .order_by(Document.version)).scalars().all()
    out = S.document(doc, job_row=_latest_job(db, doc))
    out["versions"] = [{"id": v.id, "version": v.version, "sha256": v.sha256, "created_at": S.iso(v.created_at),
                        "superseded_at": S.iso(v.superseded_at), "status": v.status} for v in versions]
    out["cited_by_findings"] = evidence_usage(db, principal.org_id, doc.id)
    return out


@router.get("/documents/{document_id}/file")
def document_file(document_id: str, principal: Principal = Depends(get_principal),
                  db: Session = Depends(get_db)) -> Response:
    doc = S.document_or_404(db, principal.org_id, document_id)
    data = get_storage().get(doc.storage_key)
    return Response(data, media_type="application/pdf", headers={
        "Content-Disposition": f'inline; filename="{doc.filename}"', "Cache-Control": "private, max-age=3600"})


@router.get("/documents/{document_id}/pages/{page}/image")
def page_image(document_id: str, page: int, scale: float = Query(default=1.5, ge=0.5, le=3.0),
               principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> Response:
    doc = S.document_or_404(db, principal.org_id, document_id)
    if not doc.page_count or not 1 <= page <= doc.page_count:
        raise HTTPException(404, "Page not found")
    storage = get_storage()
    key = f"{doc.storage_key.rsplit('/', 1)[0]}/pages/{page}@{scale:.2f}.png"
    if storage.exists(key):
        png = storage.get(key)
    else:
        try:
            png = render_page_png(storage.get(doc.storage_key), page, scale)
        except PdfError as exc:
            raise HTTPException(422, str(exc)) from exc
        storage.put(key, png, "image/png")
    return Response(png, media_type="image/png", headers={"Cache-Control": "private, max-age=86400"})


@router.get("/documents/{document_id}/passages")
def document_passages(document_id: str, page: int | None = None, principal: Principal = Depends(get_principal),
                      db: Session = Depends(get_db)) -> list[dict]:
    doc = S.document_or_404(db, principal.org_id, document_id)
    q = select(Passage).where(Passage.document_id == doc.id, Passage.org_id == principal.org_id)
    if page is not None:
        q = q.where(Passage.page == page)
    passages = db.execute(q.order_by(Passage.page, Passage.ordinal)).scalars().all()
    metrics = db.execute(select(ExtractedMetric).where(ExtractedMetric.document_id == doc.id)).scalars().all()
    by_passage: dict[str, list[dict]] = {}
    for m in metrics:
        by_passage.setdefault(m.passage_id, []).append(
            {"id": m.id, "metric_key": m.metric_key, "value": m.value, "unit": m.unit, "period_label": m.period_label})
    return [{**S.passage(p), "metrics": by_passage.get(p.id, [])} for p in passages]


@router.post("/documents/{document_id}/reprocess")
def reprocess(document_id: str, principal: Principal = Depends(require_roles(*WRITE_ROLES)),
              db: Session = Depends(get_db)) -> dict:
    doc = S.document_or_404(db, principal.org_id, document_id)
    if doc.status not in ("failed",):
        raise HTTPException(409, "Only documents that failed processing can be reprocessed. "
                                 "Upload a new version to change a processed document.")
    doc.status, doc.error = "uploaded", None
    job = enqueue(db, "process_document", {"document_id": doc.id}, org_id=principal.org_id)
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action="document.reprocessed",
                 entity_type="document", entity_id=doc.id)
    return S.document(doc, job_row=job)


@router.delete("/documents/{document_id}")
def delete_document(document_id: str, principal: Principal = Depends(require_roles(*WRITE_ROLES)),
                    db: Session = Depends(get_db)) -> dict:
    doc = S.document_or_404(db, principal.org_id, document_id)
    if evidence_usage(db, principal.org_id, doc.id):
        raise HTTPException(409, "Findings cite this document. Upload a replacement version instead of deleting it, "
                                 "so earlier assessments stay auditable.")
    get_storage().delete(doc.storage_key)
    audit.record(db, org_id=principal.org_id, actor_id=principal.user_id, action="document.deleted",
                 entity_type="document", entity_id=doc.id, data={"title": doc.title, "sha256": doc.sha256})
    db.delete(doc)
    return {"ok": True}


@router.get("/passages/{passage_id}")
def get_passage(passage_id: str, principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> dict:
    p = S.passage_or_404(db, principal.org_id, passage_id)
    doc = db.get(Document, p.document_id)
    neighbours = db.execute(select(Passage).where(Passage.document_id == p.document_id, Passage.page == p.page)
                            .order_by(Passage.ordinal)).scalars().all()
    metrics = db.execute(select(ExtractedMetric).where(ExtractedMetric.passage_id == p.id)).scalars().all()
    cited = db.execute(select(Finding.id, Finding.requirement_code, Finding.status, Finding.run_id,
                              FindingEvidence.role)
                       .join(FindingEvidence, FindingEvidence.finding_id == Finding.id)
                       .where(FindingEvidence.passage_id == p.id, Finding.org_id == principal.org_id)
                       .order_by(Finding.created_at.desc()).limit(20)).all()
    return {
        **S.passage(p, doc),
        "page_passages": [{"id": n.id, "kind": n.kind, "bbox": n.bbox, "text": n.text[:300]} for n in neighbours],
        "metrics": [{"id": m.id, "metric_key": m.metric_key, "label": m.label, "value": m.value, "unit": m.unit,
                     "normalized_value": m.normalized_value, "normalized_unit": m.normalized_unit,
                     "period_label": m.period_label, "qualifiers": m.qualifiers, "confidence": m.confidence}
                    for m in metrics],
        "cited_by": [{"finding_id": f, "requirement_code": code, "status": st, "run_id": run, "role": role}
                     for f, code, st, run, role in cited],
    }


@router.get("/search")
def search(company_id: str, q: str = Query(min_length=2, max_length=300), limit: int = Query(default=12, le=50),
           principal: Principal = Depends(get_principal), db: Session = Depends(get_db)) -> dict:
    c = S.company_or_404(db, principal.org_id, company_id)
    docs = {d.id: d for d in current_documents(db, principal.org_id, c.id) if d.status == "ready"}
    if not docs:
        return {"query": q, "results": []}
    passages = db.execute(select(Passage).where(Passage.org_id == principal.org_id,
                                                Passage.document_id.in_(list(docs)))).scalars().all()
    keys: dict[str, set[str]] = {}
    for m in db.execute(select(ExtractedMetric.passage_id, ExtractedMetric.metric_key)
                        .where(ExtractedMetric.document_id.in_(list(docs)))).all():
        keys.setdefault(m[0], set()).add(m[1])
    index = BM25Index([Doc(p.id, p.text, p.section, p.kind, frozenset(keys.get(p.id, set()))) for p in passages])
    phrases = [q] if len(q.split()) > 1 else []
    hits = index.search(q, phrases=phrases, section_terms=q.split()[:3], limit=limit)
    by_id = {p.id: p for p in passages}
    results = []
    for h in hits:
        p = by_id[h.id]
        doc = docs[p.document_id]
        results.append({**S.passage(p), "document": {"id": doc.id, "title": doc.title, "short_name": short_doc_name(doc)},
                        "match": h.explanation()})
    return {"query": q, "results": results}
