"""Request dependencies: authentication, tenancy, roles, CSRF and rate limits."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from veridion.config import get_settings
from veridion.db import get_db
from veridion.models import Membership, Organization, User
from veridion.security import decode_session_token

WRITE_ROLES = ("owner", "admin", "analyst")
REVIEW_ROLES = ("owner", "admin", "analyst", "reviewer")
ADMIN_ROLES = ("owner", "admin")
CSRF_HEADER = "x-veridion-client"


@dataclass
class Principal:
    user: User
    org: Organization
    role: str
    via_cookie: bool

    @property
    def org_id(self) -> str:
        return self.org.id

    @property
    def user_id(self) -> str:
        return self.user.id


def _token_from(request: Request) -> tuple[str | None, bool]:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip(), False
    return request.cookies.get(get_settings().session_cookie_name), True


def get_principal(request: Request, db: Session = Depends(get_db)) -> Principal:
    token, via_cookie = _token_from(request)
    payload = decode_session_token(token) if token else None
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in to continue.")
    user = db.get(User, payload["sub"])
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session is no longer valid.")
    membership = db.execute(
        select(Membership).where(Membership.user_id == user.id, Membership.org_id == payload["org"])
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "You no longer have access to this organization.")
    # CSRF: cookie-authenticated state changes must come from the Veridion web client.
    if via_cookie and request.method not in ("GET", "HEAD", "OPTIONS") and \
            request.headers.get(CSRF_HEADER) != "web":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Missing client header.")
    return Principal(user=user, org=membership.organization, role=membership.role, via_cookie=via_cookie)


def require_roles(*roles: str):
    def dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role does not allow this action.")
        return principal

    return dependency


def require_platform_admin(principal: Principal = Depends(get_principal)) -> Principal:
    if principal.user.email.lower() not in get_settings().admin_emails:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    return principal


def client_ip(request: Request) -> str:
    """The client address as resolved by uvicorn's proxy-header handling.

    X-Forwarded-For is only honoured when the connection comes from a proxy listed in
    FORWARDED_ALLOW_IPS, and then uvicorn takes the right-most untrusted hop, so a client
    cannot choose its own address by sending the header.
    """
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """In-process sliding window. Swap for Redis when running several API instances."""

    def __init__(self) -> None:
        self.hits: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: float) -> None:
        if not get_settings().rate_limit_enabled:
            return
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and q[0] <= now - window_seconds:
                q.popleft()
            if len(q) >= limit:
                retry = int(window_seconds - (now - q[0])) + 1
                raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many requests. Try again shortly.",
                                    headers={"Retry-After": str(retry)})
            q.append(now)

    def reset(self) -> None:
        with self.lock:
            self.hits.clear()


rate_limiter = RateLimiter()
