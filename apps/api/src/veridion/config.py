"""Application settings, loaded from environment variables and `.env` files."""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]  # apps/api
REPO_ROOT = API_ROOT.parents[1]

# Later files override earlier ones: repo-level .env first, then apps/api/.env.
_ENV_FILES = (REPO_ROOT / ".env", API_ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILES, env_file_encoding="utf-8", extra="ignore")

    veridion_env: Literal["development", "production", "test"] = "development"

    secret_key: str = ""
    database_url: str = f"sqlite:///{API_ROOT / 'var' / 'veridion.db'}"
    cors_origins: str = "http://localhost:3000"
    embedded_worker: bool = True
    web_concurrency: int = 1  # API server processes for `veridion serve`
    db_pool_size: int = 5  # PostgreSQL connections kept open per process
    db_max_overflow: int = 10  # extra connections a process may open under load
    allow_registration: bool = True  # false: new workspaces only by invitation (pilot phase)
    forwarded_allow_ips: str = "127.0.0.1,::1"  # proxies whose X-Forwarded-For is trusted (IPs or CIDRs)
    cookie_secure: bool = False
    session_cookie_name: str = "veridion_session"
    session_ttl_hours: int = 24 * 7
    platform_admin_emails: str = ""

    storage_backend: Literal["local", "s3"] = "local"
    storage_dir: Path = API_ROOT / "var" / "storage"
    s3_bucket: str = ""
    s3_endpoint_url: str = ""
    s3_region: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""

    max_upload_mb: int = 50
    ocr_enabled: bool = True

    llm_provider: Literal["groq", "openai_compatible", "none"] = "none"
    groq_api_key: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "openai/gpt-oss-120b"
    llm_max_concurrency: int = 2
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 4

    catalog_dir: Path = API_ROOT / "catalog"
    worker_poll_seconds: float = 1.0

    rate_limit_enabled: bool = True

    @field_validator("storage_dir", "catalog_dir", mode="before")
    @classmethod
    def _resolve_relative(cls, value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else (API_ROOT / path).resolve()

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalise_database_url(cls, value: str) -> str:
        # Hosting platforms (Render, Heroku, Railway) hand out postgres:// or postgresql:// URLs;
        # SQLAlchemy needs the driver named to use psycopg 3.
        for scheme in ("postgres://", "postgresql://"):
            if value.startswith(scheme):
                return "postgresql+psycopg://" + value[len(scheme):]
        # Make relative SQLite paths independent of the working directory.
        prefix = "sqlite:///"
        if value.startswith(prefix) and not value.startswith("sqlite:////") and ":memory:" not in value:
            rel = value[len(prefix):]
            if not Path(rel).is_absolute():
                return prefix + str((API_ROOT / rel).resolve())
        return value

    # --- derived values ---------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.veridion_env == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def admin_emails(self) -> set[str]:
        return {e.strip().lower() for e in self.platform_admin_emails.split(",") if e.strip()}

    @property
    def llm_enabled(self) -> bool:
        return self.llm_provider != "none" and bool(self.effective_llm_api_key or self.llm_base_url)

    @property
    def effective_llm_base_url(self) -> str:
        if self.llm_base_url:
            return self.llm_base_url.rstrip("/")
        if self.llm_provider == "groq":
            return "https://api.groq.com/openai/v1"
        return ""

    @property
    def effective_llm_api_key(self) -> str:
        if self.llm_provider == "groq":
            return self.groq_api_key or self.llm_api_key
        return self.llm_api_key

    @property
    def llm_provider_label(self) -> str:
        if self.llm_provider == "groq":
            return "groq"
        return self.effective_llm_base_url or "none"


def _ensure_secret(settings: Settings) -> None:
    if settings.secret_key:
        return
    if settings.is_production:
        raise RuntimeError("SECRET_KEY must be set in production.")
    # Development: persist a random key so sessions survive restarts.
    key_file = API_ROOT / "var" / ".secret_key"
    key_file.parent.mkdir(parents=True, exist_ok=True)
    if key_file.exists():
        settings.secret_key = key_file.read_text().strip()
    else:
        settings.secret_key = secrets.token_urlsafe(48)
        key_file.write_text(settings.secret_key)
        key_file.chmod(0o600)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        settings = Settings()
        _ensure_secret(settings)
        _settings = settings
    return _settings


def configure(**values: object) -> Settings:
    """Replace the active settings (used by tests and CLI commands)."""
    global _settings
    settings = Settings(**values)  # type: ignore[arg-type]
    _ensure_secret(settings)
    _settings = settings
    return settings


__all__ = ["API_ROOT", "REPO_ROOT", "Settings", "configure", "get_settings"]
