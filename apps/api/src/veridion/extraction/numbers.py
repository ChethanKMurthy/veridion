"""Number parsing for disclosure text and table cells."""

from __future__ import annotations

import re

SCALE_WORDS = {
    "thousand": 1e3,
    "million": 1e6,
    "mn": 1e6,
    "billion": 1e9,
    "bn": 1e9,
    "lakh": 1e5,
    "lakhs": 1e5,
    "crore": 1e7,
    "crores": 1e7,
}

# 12,450 · 12 450 (thin/nbsp separators) · 1,234.5 · 0.82 · (1,234) for negatives · −3.1
NUMBER_RE = re.compile(
    r"(?<![\w.,])"
    r"(?P<sign>[-−–])?"
    r"(?P<paren>\()?"
    r"(?P<num>\d{1,3}(?:[,\u00a0\u202f\u2009]\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?(paren)\))"
    r"(?:\s*(?P<scale>thousand|million|billion|mn|bn|lakhs?|crores?)\b)?",
    re.IGNORECASE,
)

YEAR_RE = re.compile(r"^(?:19|20)\d{2}$")
SPACED_THOUSANDS_RE = re.compile(r"^[-−(]?\d{1,3}(?: \d{3})+(?:\.\d+)?\)?$")


def parse_number(raw: str) -> float | None:
    """Parse a single numeric cell such as '12,450', '(310)', '1.2 million' or '—'."""
    text = raw.strip().replace("−", "-")
    if not text or text in {"-", "–", "—", "n/a", "N/A", "na", "NA", "nd", "n.d."}:
        return None
    if SPACED_THOUSANDS_RE.match(text):  # a whole cell such as "12 450"
        text = text.replace(" ", "")
    m = NUMBER_RE.search(text)
    if not m:
        return None
    return _value(m)


def _value(m: re.Match[str]) -> float:
    num = re.sub(r"[,\u00a0\u202f\u2009]", "", m.group("num"))
    value = float(num)
    scale = m.group("scale")
    if scale:
        value *= SCALE_WORDS[scale.lower()]
    if m.group("sign") or m.group("paren"):
        value = -value
    return value


def iter_numbers(text: str):
    """Yield (value, start, end, match) for every number in `text`."""
    for m in NUMBER_RE.finditer(text):
        yield _value(m), m.start(), m.end(), m


def looks_like_year(raw: str) -> bool:
    return bool(YEAR_RE.match(raw.strip()))
