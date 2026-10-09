"""Reporting-period detection and normalisation.

A period is represented by its first and last day. Labels are canonical:
`FY2025` always means the financial year *ending* in 2025, whose dates depend
on the company's fiscal year end (e.g. 1 Apr 2024 – 31 Mar 2025 for a March
year end, or 1 Jan – 31 Dec 2025 for a calendar year).
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta

MONTHS = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
MONTHS.update({name.lower(): i for i, name in enumerate(calendar.month_abbr) if name})
MONTHS["sept"] = 9

_MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?"


def _date_pattern(name: str) -> str:
    """'31 December 2025' or 'December 31, 2025' with group names prefixed by `name`."""
    dmy = rf"(?P<{name}d>\d{{1,2}})(?:st|nd|rd|th)?\s+(?P<{name}m>{_MONTH})\s*,?\s+(?P<{name}y>(?:19|20)\d{{2}})"
    mdy = rf"(?P<{name}m2>{_MONTH})\s+(?P<{name}d2>\d{{1,2}})(?:st|nd|rd|th)?\s*,?\s+(?P<{name}y2>(?:19|20)\d{{2}})"
    return rf"(?:{dmy}|{mdy})"


RANGE_RE = re.compile(
    rf"(?:from\s+)?{_date_pattern('a')}\s*(?:to|until|–|-|—|through)\s*{_date_pattern('b')}", re.IGNORECASE
)
YEAR_ENDED_RE = re.compile(
    rf"(?:year|twelve months|12 months|period|financial year|fiscal year)\s+(?:ended|ending)\s+(?:on\s+)?{_date_pattern('e')}",
    re.IGNORECASE,
)
FY_SPLIT_RE = re.compile(r"\bFY\s?(?P<a>(?:19|20)\d{2})\s?[/–-]\s?(?P<b>\d{2,4})\b", re.IGNORECASE)
FY_RE = re.compile(r"\b(?:FY|fiscal\s+(?:year\s+)?|financial\s+year\s+)\s?(?P<y>(?:19|20)\d{2}|\d{2})\b", re.IGNORECASE)
CY_RE = re.compile(r"\b(?:CY\s?|calendar\s+year\s+)(?P<y>(?:19|20)\d{2})\b", re.IGNORECASE)
SPLIT_YEAR_RE = re.compile(r"\b(?P<a>(?:19|20)\d{2})\s?[/–-]\s?(?P<b>\d{2})\b")
BARE_YEAR_RE = re.compile(r"(?<![\w.,/-])(?P<y>(?:19|20)\d{2})(?![\w/-]|[.,]\d|\s?%)")


@dataclass(frozen=True)
class Period:
    label: str
    start: date
    end: date
    explicit: bool  # True when dates were stated, False when inferred from a label
    raw: str

    def overlaps(self, other: Period) -> bool:
        return self.start <= other.end and other.start <= self.end

    def same_as(self, other: Period) -> bool:
        return self.start == other.start and self.end == other.end

    @property
    def end_month(self) -> int:
        return self.end.month


def _mk_date(m: re.Match[str], name: str) -> date | None:
    groups = m.groupdict()
    if groups.get(f"{name}d"):
        d, mon, y = groups[f"{name}d"], groups[f"{name}m"], groups[f"{name}y"]
    elif groups.get(f"{name}d2"):
        d, mon, y = groups[f"{name}d2"], groups[f"{name}m2"], groups[f"{name}y2"]
    else:
        return None
    month = MONTHS.get(mon.lower().rstrip("."))
    if not month:
        return None
    try:
        return date(int(y), month, int(d))
    except ValueError:
        return None


def parse_fye(fiscal_year_end: str | None) -> tuple[int, int]:
    """'03-31' → (3, 31). Defaults to a calendar year."""
    try:
        month, day = (int(p) for p in (fiscal_year_end or "12-31").split("-"))
        return month, day
    except ValueError:
        return 12, 31


def fiscal_year(end_year: int, fiscal_year_end: str | None = "12-31") -> Period:
    month, day = parse_fye(fiscal_year_end)
    day = min(day, calendar.monthrange(end_year, month)[1])
    end = date(end_year, month, day)
    start = _year_start_for_end(end)
    return Period(f"FY{end_year}", start, end, explicit=False, raw=f"FY{end_year}")


def _year_start_for_end(end: date) -> date:
    # The day after the same date one year earlier.
    try:
        prev = end.replace(year=end.year - 1)
    except ValueError:  # 29 Feb
        prev = end.replace(year=end.year - 1, day=28)
    return prev + timedelta(days=1)


def period_from_dates(start: date, end: date, raw: str) -> Period:
    return Period(f"FY{end.year}", start, end, explicit=True, raw=raw)


def _expand_two_digit(a: int, b: str) -> int:
    if len(b) == 4:
        return int(b)
    century = a // 100 * 100
    year = century + int(b)
    return year if year > a else year + 100


def find_periods(text: str, fiscal_year_end: str | None = "12-31") -> list[tuple[Period, int, int]]:
    """Return every period mentioned in `text` with its character span, most explicit first."""
    found: list[tuple[Period, int, int]] = []
    taken: list[tuple[int, int]] = []

    def free(s: int, e: int) -> bool:
        return all(e <= ts or s >= te for ts, te in taken)

    for m in RANGE_RE.finditer(text):
        a = _mk_date(m, "a")
        b = _mk_date(m, "b")
        if a and b and a < b:
            found.append((period_from_dates(a, b, m.group(0)), m.start(), m.end()))
            taken.append((m.start(), m.end()))
    for m in YEAR_ENDED_RE.finditer(text):
        if not free(m.start(), m.end()):
            continue
        e = _mk_date(m, "e")
        if e:
            found.append((period_from_dates(_year_start_for_end(e), e, m.group(0)), m.start(), m.end()))
            taken.append((m.start(), m.end()))
    for rx in (FY_SPLIT_RE,):
        for m in rx.finditer(text):
            if not free(m.start(), m.end()):
                continue
            a = int(m.group("a"))
            end_year = _expand_two_digit(a, m.group("b"))
            p = fiscal_year(end_year, fiscal_year_end)
            found.append((Period(p.label, p.start, p.end, False, m.group(0)), m.start(), m.end()))
            taken.append((m.start(), m.end()))
    for m in CY_RE.finditer(text):
        if not free(m.start(), m.end()):
            continue
        y = int(m.group("y"))
        found.append((Period(f"CY{y}", date(y, 1, 1), date(y, 12, 31), False, m.group(0)), m.start(), m.end()))
        taken.append((m.start(), m.end()))
    for m in FY_RE.finditer(text):
        if not free(m.start(), m.end()):
            continue
        y = m.group("y")
        year = int(y) if len(y) == 4 else 2000 + int(y)
        p = fiscal_year(year, fiscal_year_end)
        found.append((Period(p.label, p.start, p.end, False, m.group(0)), m.start(), m.end()))
        taken.append((m.start(), m.end()))
    for m in SPLIT_YEAR_RE.finditer(text):
        if not free(m.start(), m.end()):
            continue
        a = int(m.group("a"))
        end_year = _expand_two_digit(a, m.group("b"))
        if end_year - a == 1:
            p = fiscal_year(end_year, fiscal_year_end)
            found.append((Period(p.label, p.start, p.end, False, m.group(0)), m.start(), m.end()))
            taken.append((m.start(), m.end()))
    return found


def find_bare_years(text: str, fiscal_year_end: str | None = "12-31") -> list[tuple[Period, int, int]]:
    out = []
    for m in BARE_YEAR_RE.finditer(text):
        p = fiscal_year(int(m.group("y")), fiscal_year_end)
        out.append((Period(p.label, p.start, p.end, False, m.group(0)), m.start(), m.end()))
    return out


def parse_period_label(label: str, fiscal_year_end: str | None = "12-31") -> Period | None:
    """Parse a column header or user-provided label ('FY2025', '2025', 'FY2024/25')."""
    label = label.strip()
    hits = find_periods(label, fiscal_year_end)
    if hits:
        return hits[0][0]
    bare = find_bare_years(label, fiscal_year_end)
    if len(bare) == 1:
        return bare[0][0]
    return None


def describe(period: Period) -> str:
    return f"{period.start:%d %b %Y} – {period.end:%d %b %Y}"
