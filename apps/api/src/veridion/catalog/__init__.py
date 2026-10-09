"""Loading and validating the versioned requirement catalogue.

Catalogue files live in `apps/api/catalog/<set key>/<version>.yaml`. Each file is
validated (including every regular expression) and loaded into the database.
A loaded version is immutable: if its content changes after assessment runs
have used it, loading fails and the author must publish a new version.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from veridion.config import get_settings
from veridion.ids import sha256_text
from veridion.models import AssessmentRun, Requirement, RequirementSet

log = logging.getLogger("veridion.catalog")


class Check(BaseModel):
    type: Literal["metric", "metric_period", "pattern", "any_of", "conditional"]
    metric_keys: list[str] = Field(default_factory=list)
    weak_metric_keys: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    context: list[str] = Field(default_factory=list)
    checks: list[Check] = Field(default_factory=list)
    when: Check | None = None
    then: Check | None = None

    @field_validator("patterns", "context")
    @classmethod
    def _valid_regex(cls, values: list[str]) -> list[str]:
        for pattern in values:
            try:
                re.compile(pattern, re.IGNORECASE)
            except re.error as exc:
                raise ValueError(f"Invalid regular expression {pattern!r}: {exc}") from exc
        return values

    @model_validator(mode="after")
    def _shape(self) -> Check:
        if self.type in ("metric", "metric_period") and not self.metric_keys:
            raise ValueError(f"{self.type} check requires metric_keys")
        if self.type == "pattern" and not self.patterns:
            raise ValueError("pattern check requires patterns")
        if self.type == "any_of" and not self.checks:
            raise ValueError("any_of check requires checks")
        if self.type == "conditional" and (self.when is None or self.then is None):
            raise ValueError("conditional check requires when and then")
        return self


class ActionTemplate(BaseModel):
    title: str
    detail: str = ""
    effort: Literal["low", "medium", "high"] = "medium"
    depends_on: list[str] = Field(default_factory=list)


class Element(BaseModel):
    key: str
    label: str
    weight: float = 1.0
    check: Check
    action: ActionTemplate


class CatalogRequirement(BaseModel):
    code: str
    display_code: str
    title: str
    topic: str
    importance: int = Field(default=2, ge=1, le=3)
    summary: str
    applicability: str | None = None
    source_reference: str
    source_url: str | None = None
    metric_keys: list[str] = Field(default_factory=list)
    search_terms: list[str] = Field(default_factory=list)
    related_terms: list[str] = Field(default_factory=list)
    elements: list[Element]

    @model_validator(mode="after")
    def _unique_elements(self) -> CatalogRequirement:
        keys = [e.key for e in self.elements]
        if len(keys) != len(set(keys)):
            raise ValueError(f"Duplicate element keys in {self.code}: {keys}")
        return self


class Standard(BaseModel):
    name: str
    url: str | None = None


class ChangelogEntry(BaseModel):
    version: str
    date: date
    changes: list[str]


class CatalogSet(BaseModel):
    key: str
    version: str
    title: str
    framework: str
    review_status: Literal["reviewed", "draft"] = "draft"
    description: str | None = None
    standards: list[Standard] = Field(default_factory=list)
    effective_from: date | None = None
    effective_to: date | None = None
    effective_rule: str | None = None
    supersedes: str | None = None
    succeeded_by: str | None = None
    notes: str | None = None
    changelog: list[ChangelogEntry] = Field(default_factory=list)
    requirements: list[CatalogRequirement]

    @property
    def id(self) -> str:
        return f"{self.key}@{self.version}"


def _canonical(data: object) -> str:
    return json.dumps(data, sort_keys=True, default=str, separators=(",", ":"))


def parse_file(path: Path) -> CatalogSet:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw.pop("shared", None)  # YAML anchors only
    catalog = CatalogSet.model_validate(raw)
    if path.stem != catalog.version or path.parent.name != catalog.key:
        raise ValueError(f"{path}: file location must be <key>/<version>.yaml")
    return catalog


def discover(catalog_dir: Path | None = None) -> list[CatalogSet]:
    root = catalog_dir or get_settings().catalog_dir
    return [parse_file(p) for p in sorted(root.glob("*/*.yaml"))]


def set_status(rs: RequirementSet | CatalogSet, on: date | None = None) -> str:
    """'in_force', 'upcoming' or 'withdrawn' on the given date (default today)."""
    on = on or date.today()
    if rs.effective_from and on < rs.effective_from:
        return "upcoming"
    if rs.effective_to and on > rs.effective_to:
        return "withdrawn"
    return "in_force"


def load_catalog(session: Session, catalog_dir: Path | None = None) -> list[str]:
    """Load every catalogue file into the database. Returns ids that were added or updated."""
    changed: list[str] = []
    for catalog in discover(catalog_dir):
        set_payload = catalog.model_dump(mode="json", exclude={"requirements"})
        req_payloads = [r.model_dump(mode="json") for r in catalog.requirements]
        content_hash = sha256_text(_canonical({"set": set_payload, "requirements": req_payloads}))

        existing = session.get(RequirementSet, catalog.id)
        if existing is not None:
            if existing.content_hash == content_hash:
                continue
            used = session.execute(
                select(AssessmentRun.id).where(AssessmentRun.requirement_set_id == catalog.id).limit(1)
            ).first()
            if used:
                raise RuntimeError(
                    f"Catalogue {catalog.id} changed after assessment runs used it. "
                    "Publish the change as a new version instead."
                )
            log.warning("Reloading unused catalogue %s with new content", catalog.id)
            for req in list(existing.requirements):
                session.delete(req)
            session.delete(existing)
            session.flush()

        rs = RequirementSet(
            id=catalog.id, key=catalog.key, version=catalog.version, title=catalog.title,
            framework=catalog.framework, description=catalog.description,
            standards=[s.model_dump() for s in catalog.standards],
            effective_from=catalog.effective_from, effective_to=catalog.effective_to,
            effective_rule=catalog.effective_rule, review_status=catalog.review_status,
            changelog=[c.model_dump(mode="json") for c in catalog.changelog],
            supersedes=catalog.supersedes, succeeded_by=catalog.succeeded_by, notes=catalog.notes,
            content_hash=content_hash,
        )
        session.add(rs)
        for ordinal, (req, payload) in enumerate(zip(catalog.requirements, req_payloads, strict=True)):
            session.add(Requirement(
                id=f"{catalog.id}/{req.code}", set_id=catalog.id, code=req.code,
                display_code=req.display_code, title=req.title, topic=req.topic, summary=req.summary.strip(),
                applicability=req.applicability, importance=req.importance,
                elements=[e.model_dump(mode="json") for e in req.elements],
                metric_keys=req.metric_keys, search_terms=req.search_terms, related_terms=req.related_terms,
                source_reference=req.source_reference, source_url=req.source_url, ordinal=ordinal,
                content_hash=sha256_text(_canonical(payload)),
            ))
        changed.append(catalog.id)
    session.flush()
    return changed
