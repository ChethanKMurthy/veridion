"""Settings parsing."""

from __future__ import annotations

import pytest

from veridion.config import Settings


@pytest.mark.parametrize("url", [
    "postgres://user:pw@db.internal:5432/veridion",
    "postgresql://user:pw@db.internal:5432/veridion",
    "postgresql+psycopg://user:pw@db.internal:5432/veridion",
])
def test_platform_postgres_urls_use_psycopg(url):
    assert Settings(database_url=url).database_url == "postgresql+psycopg://user:pw@db.internal:5432/veridion"


def test_relative_sqlite_paths_are_anchored_to_the_api_directory():
    url = Settings(database_url="sqlite:///./var/x.db").database_url
    assert url.startswith("sqlite:////") and url.endswith("/apps/api/var/x.db")
