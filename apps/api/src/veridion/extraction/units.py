"""Unit recognition and normalisation.

Every unit belongs to a family with a canonical base unit:

    emissions → tCO2e    energy → MWh    volume → m3    mass → t
    percent   → %        rate   → (not converted)       currency → (not converted)

Values are only ever compared within a family, after conversion to the base unit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_GJ_TO_MWH = 1 / 3.6  # 1 MWh = 3.6 GJ


@dataclass(frozen=True)
class Unit:
    symbol: str
    family: str
    factor: float  # multiply a value in this unit to obtain the family base unit

    @property
    def base(self) -> str:
        return FAMILY_BASE[self.family]


FAMILY_BASE = {
    "emissions": "tCO2e",
    "energy": "MWh",
    "volume": "m3",
    "mass": "t",
    "percent": "%",
    "rate": "rate",
    "currency": "currency",
}

_CO2 = r"CO\s?(?:2|₂)\s?[-‑]?\s?(?:e|eq|equivalents?|-?e(?:q)?)?\.?"
_CO2E = rf"(?:{_CO2})"
_OF = r"(?:\s+of)?"

# (regex, Unit). Longer / more specific patterns first.
_UNIT_PATTERNS: list[tuple[str, Unit]] = [
    # emissions
    (rf"million\s+(?:metric\s+)?(?:tonnes|tons){_OF}\s+{_CO2E}", Unit("MtCO2e", "emissions", 1e6)),
    (rf"thousand\s+(?:metric\s+)?(?:tonnes|tons){_OF}\s+{_CO2E}", Unit("ktCO2e", "emissions", 1e3)),
    (rf"(?:'000|’000)\s*(?:tonnes|t)\s*{_CO2E}", Unit("ktCO2e", "emissions", 1e3)),
    (r"(?:metric\s+)?(?:tonnes|tons)\s+of\s+carbon\s+dioxide\s+equivalents?", Unit("tCO2e", "emissions", 1.0)),
    (rf"(?:metric\s+)?(?:tonnes|tons){_OF}\s+{_CO2E}", Unit("tCO2e", "emissions", 1.0)),
    (rf"Mt\s?{_CO2E}", Unit("MtCO2e", "emissions", 1e6)),
    (rf"kt\s?{_CO2E}", Unit("ktCO2e", "emissions", 1e3)),
    (rf"kg\s?{_CO2E}", Unit("kgCO2e", "emissions", 1e-3)),
    (rf"t\s?{_CO2E}", Unit("tCO2e", "emissions", 1.0)),
    # energy
    (r"TWh\b", Unit("TWh", "energy", 1e6)),
    (r"GWh\b", Unit("GWh", "energy", 1e3)),
    (r"MWh\b|megawatt[\s-]hours?", Unit("MWh", "energy", 1.0)),
    (r"kWh\b|kilowatt[\s-]hours?", Unit("kWh", "energy", 1e-3)),
    (r"PJ\b|petajoules?", Unit("PJ", "energy", 1e6 * _GJ_TO_MWH)),
    (r"TJ\b|terajoules?", Unit("TJ", "energy", 1e3 * _GJ_TO_MWH)),
    (r"GJ\b|gigajoules?", Unit("GJ", "energy", _GJ_TO_MWH)),
    (r"MJ\b|megajoules?", Unit("MJ", "energy", 1e-3 * _GJ_TO_MWH)),
    # volume (water)
    (r"million\s+(?:m3|m³|cubic\s+met(?:re|er)s)", Unit("million m3", "volume", 1e6)),
    (r"(?:thousand|'000|’000)\s+(?:m3|m³|cubic\s+met(?:re|er)s)", Unit("thousand m3", "volume", 1e3)),
    (r"megalit(?:re|er)s?\b|\bML\b", Unit("ML", "volume", 1e3)),
    (r"m3\b|m³|cubic\s+met(?:re|er)s", Unit("m3", "volume", 1.0)),
    # mass (waste, materials)
    (r"thousand\s+(?:metric\s+)?(?:tonnes|tons)\b|\bkt\b", Unit("kt", "mass", 1e3)),
    (r"(?:metric\s+)?(?:tonnes|tons)\b", Unit("t", "mass", 1.0)),
    (r"t\b(?!\s?CO)", Unit("t", "mass", 1.0)),
    # percent
    (r"%|per\s?cent\b|percent\b", Unit("%", "percent", 1.0)),
]

_COMPILED = [(re.compile(rf"(?<![A-Za-z])(?:{pat})", re.IGNORECASE), unit) for pat, unit in _UNIT_PATTERNS]

# A unit at the very start of a string (used right after a number).
_LEADING = [(re.compile(rf"^\s*(?:{pat})", re.IGNORECASE), unit) for pat, unit in _UNIT_PATTERNS]


def match_unit_at_start(text: str) -> tuple[Unit, int] | None:
    """Return the unit that starts `text` (ignoring whitespace) and the match length."""
    for rx, unit in _LEADING:
        m = rx.match(text)
        if m:
            return unit, m.end()
    return None


def find_unit(text: str) -> Unit | None:
    """Find the first recognisable unit anywhere in `text` (e.g. a table row label)."""
    best: tuple[int, Unit] | None = None
    for rx, unit in _COMPILED:
        m = rx.search(text)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), unit)
    return best[1] if best else None


def unit_from_symbol(symbol: str) -> Unit | None:
    for rx, unit in _LEADING:
        m = rx.match(symbol)
        if m and m.end() == len(symbol.strip()):
            return unit
    return None


def normalize(value: float, unit: Unit) -> tuple[float, str]:
    if unit.family in ("rate", "currency"):
        return value, unit.symbol
    return value * unit.factor, unit.base


def convert(value: float, from_unit: Unit, to_symbol: str) -> float | None:
    target = unit_from_symbol(to_symbol)
    if target is None or target.family != from_unit.family:
        return None
    return value * from_unit.factor / target.factor
