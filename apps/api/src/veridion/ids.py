"""Identifier helpers.

Entity IDs are prefixed and time-sortable (`doc_01J…`), which keeps logs and
exports readable. Evidence IDs are deterministic so re-processing the same
document version yields the same IDs, preserving links from earlier findings.
"""

from __future__ import annotations

import hashlib
import os
import time

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def _encode(value: int, length: int) -> str:
    chars = []
    for _ in range(length):
        chars.append(_CROCKFORD[value & 31])
        value >>= 5
    return "".join(reversed(chars))


def ulid() -> str:
    """26-character ULID: 48-bit millisecond timestamp + 80 random bits."""
    ts = int(time.time() * 1000)
    rand = int.from_bytes(os.urandom(10), "big")
    return _encode(ts, 10) + _encode(rand, 16)


def new_id(prefix: str) -> str:
    return f"{prefix}_{ulid().lower()}"


def evidence_id(document_id: str, page: int, ordinal: int, text: str) -> str:
    digest = hashlib.sha256(f"{document_id}|{page}|{ordinal}|{text}".encode()).hexdigest()
    return f"ev_{digest[:20]}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
