"""Shared request field types."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator

_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s.]{2,63}$")


def _email(value: str) -> str:
    value = value.strip().lower()
    if len(value) > 320 or not _EMAIL.match(value):
        raise ValueError("Enter a valid email address")
    return value


# Format-only validation. Deliverability is not checked because Veridion does not send email yet;
# reserved domains such as .example are accepted for demo and test accounts.
Email = Annotated[str, AfterValidator(_email)]
