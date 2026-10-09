from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from veridion.config import API_ROOT, configure

SAMPLES = API_ROOT / "samples" / "pdfs"


@pytest.fixture(scope="session", autouse=True)
def sample_pdfs() -> Path:
    from veridion.samples.content import ALDERMERE_AR_V2, COMPANIES
    from veridion.samples.generator import write_samples

    needed = [d.slug for c in COMPANIES for d in c.documents] + [ALDERMERE_AR_V2.slug]
    if not all((SAMPLES / f"{s}.pdf").exists() for s in needed):
        write_samples(SAMPLES)
    return SAMPLES


@pytest.fixture(autouse=True)
def isolated_env(tmp_path: Path) -> Iterator[Path]:
    """Every test gets its own database, storage directory and a rules-only configuration."""
    from veridion import db, llm, storage
    from veridion.api.deps import rate_limiter

    configure(
        veridion_env="test",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        storage_dir=str(tmp_path / "storage"),
        llm_provider="none",
        embedded_worker=False,
        secret_key="test-secret-key-for-signing-sessions",
        rate_limit_enabled=False,
        platform_admin_emails="ops@veridion.test",
    )
    db.reset_engine()
    storage.reset_storage()
    llm.set_provider(None, explicit=False)
    rate_limiter.reset()
    db.create_all()
    yield tmp_path
    db.reset_engine()
    shutil.rmtree(tmp_path / "storage", ignore_errors=True)


@pytest.fixture
def session():
    from veridion.catalog import load_catalog
    from veridion.db import session_factory

    s = session_factory()()
    load_catalog(s)
    s.commit()
    try:
        yield s
        s.commit()
    finally:
        s.close()


@pytest.fixture
def org(session):
    from veridion.models import Organization

    o = Organization(name="Test Org", slug="test-org", plan="enterprise")
    session.add(o)
    session.commit()
    return o


def add_sample_company(session, org, slug: str):
    """Create a sample company with its documents and process them synchronously."""
    from veridion.models import Company
    from veridion.samples.content import COMPANIES
    from veridion.services.documents import create_document, process_document

    sample = next(c for c in COMPANIES if c.slug == slug)
    company = Company(org_id=org.id, name=sample.name, industry=sample.industry, fiscal_year_end=sample.fiscal_year_end,
                      is_sample=True)
    session.add(company)
    session.flush()
    for d in sample.documents:
        doc, _ = create_document(session, org_id=org.id, company=company, data=(SAMPLES / f"{d.slug}.pdf").read_bytes(),
                                 filename=f"{d.slug}.pdf", title=d.title, doc_type=d.doc_type,
                                 period_label=d.period_label, published_on=None, uploaded_by=None)
        process_document(session, doc)
    session.commit()
    return company


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from veridion.main import create_app

    with TestClient(create_app()) as c:
        c.headers.update({"X-Veridion-Client": "web"})
        yield c


def register(client, email: str = "analyst@example.com", org: str = "Acme Advisory", password: str = "a-long-password"):
    r = client.post("/api/v1/auth/register", json={"name": "Test User", "email": email, "password": password,
                                                    "organization": org})
    assert r.status_code == 201, r.text
    return r.json()


def tesseract_available() -> bool:
    return shutil.which("tesseract") is not None
