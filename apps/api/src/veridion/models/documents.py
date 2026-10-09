"""Companies, source documents and the evidence extracted from them."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veridion.db import Base, utcnow
from veridion.ids import new_id
from veridion.models.types import ID_LEN, JSONType

DOC_TYPES = ("annual_report", "sustainability_report", "policy", "data_sheet", "other")
DOC_STATUSES = ("uploaded", "processing", "ready", "failed")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("cmp"))
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(80))
    size_band: Mapped[str | None] = mapped_column(String(40))
    # Month-day the financial year ends, e.g. "12-31" or "03-31".
    fiscal_year_end: Mapped[str] = mapped_column(String(5), default="12-31")
    website: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    # Fictional sample companies are always labelled as such in the interface.
    is_sample: Mapped[bool] = mapped_column(default=False)
    created_by: Mapped[str | None] = mapped_column(String(ID_LEN))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    documents: Mapped[list[Document]] = relationship(back_populates="company", cascade="all, delete-orphan")


class CompanyPeer(Base):
    __tablename__ = "company_peers"

    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    peer_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(ID_LEN), index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Document(Base):
    """One immutable version of a source file. New uploads in the same lineage create new versions."""

    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_company_lineage", "company_id", "lineage_id"),)

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("doc"))
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    lineage_id: Mapped[str] = mapped_column(String(ID_LEN))
    version: Mapped[int] = mapped_column(Integer, default=1)

    title: Mapped[str] = mapped_column(String(300))
    doc_type: Mapped[str] = mapped_column(String(40), default="other")
    filename: Mapped[str] = mapped_column(String(300))
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")
    storage_key: Mapped[str] = mapped_column(String(500))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int | None] = mapped_column(Integer)
    # [[width, height], ...] in PDF points, used to place highlights over rendered pages.
    page_sizes: Mapped[list] = mapped_column(JSONType, default=list)

    period_label: Mapped[str | None] = mapped_column(String(40))
    period_start: Mapped[date | None] = mapped_column(default=None)
    period_end: Mapped[date | None] = mapped_column(default=None)
    published_on: Mapped[date | None] = mapped_column(default=None)
    source_url: Mapped[str | None] = mapped_column(String(500))

    status: Mapped[str] = mapped_column(String(20), default="uploaded")
    error: Mapped[str | None] = mapped_column(Text)
    ocr_pages: Mapped[list] = mapped_column(JSONType, default=list)
    processing_stats: Mapped[dict] = mapped_column(JSONType, default=dict)
    pipeline_version: Mapped[str | None] = mapped_column(String(40))
    extraction_version: Mapped[str | None] = mapped_column(String(40))

    is_sample: Mapped[bool] = mapped_column(default=False)
    uploaded_by: Mapped[str | None] = mapped_column(String(ID_LEN))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(default=None)
    # Set when a newer version of the same lineage is uploaded.
    superseded_at: Mapped[datetime | None] = mapped_column(default=None)
    superseded_by: Mapped[str | None] = mapped_column(String(ID_LEN))

    company: Mapped[Company] = relationship(back_populates="documents")


class Passage(Base):
    """An evidence unit: a paragraph, heading, list item, table or table row on one page."""

    __tablename__ = "passages"
    __table_args__ = (Index("ix_passages_document_page", "document_id", "page"),)

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True)  # deterministic ev_…
    org_id: Mapped[str] = mapped_column(String(ID_LEN), index=True)
    company_id: Mapped[str] = mapped_column(String(ID_LEN), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    page: Mapped[int] = mapped_column(Integer)
    ordinal: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(20))  # paragraph | heading | list_item | table | table_row
    section: Mapped[str | None] = mapped_column(String(300))
    text: Mapped[str] = mapped_column(Text)
    bbox: Mapped[list] = mapped_column(JSONType, default=list)  # [x0, y0, x1, y1] in PDF points
    extraction_method: Mapped[str] = mapped_column(String(20), default="text")  # text | ocr | table
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    table_ref: Mapped[str | None] = mapped_column(String(60))
    cells: Mapped[dict | None] = mapped_column(JSONType, default=None)


class ExtractedMetric(Base):
    """A typed value (with unit and period) extracted from a passage."""

    __tablename__ = "extracted_metrics"
    __table_args__ = (Index("ix_extracted_metrics_company_key", "company_id", "metric_key"),)

    id: Mapped[str] = mapped_column(String(ID_LEN), primary_key=True, default=lambda: new_id("met"))
    org_id: Mapped[str] = mapped_column(String(ID_LEN), index=True)
    company_id: Mapped[str] = mapped_column(String(ID_LEN))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    passage_id: Mapped[str] = mapped_column(ForeignKey("passages.id", ondelete="CASCADE"), index=True)

    metric_key: Mapped[str] = mapped_column(String(60))
    label: Mapped[str | None] = mapped_column(String(300))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(40))
    normalized_value: Mapped[float | None] = mapped_column(Float)
    normalized_unit: Mapped[str | None] = mapped_column(String(40))
    period_label: Mapped[str | None] = mapped_column(String(40))
    period_start: Mapped[date | None] = mapped_column(default=None)
    period_end: Mapped[date | None] = mapped_column(default=None)
    # e.g. {"method": "location-based", "boundary": "operational control", "restated": true}
    qualifiers: Mapped[dict] = mapped_column(JSONType, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    method: Mapped[str] = mapped_column(String(20), default="text")  # text | table | llm
    raw_text: Mapped[str | None] = mapped_column(Text)
