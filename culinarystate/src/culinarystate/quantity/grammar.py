r"""
Quantity grammar v0 (block B10, master prompt Part J3 step 1): raw span → structure.

Handles: integers, decimals, ASCII and Unicode fractions, mixed numbers ("1 1/2",
"1½"), ranges ("2-3", "2–3", "2 to 3", "2 or 3"), approximations ("about", "~"),
packages ("1 (400 g) can", "2 x 400 g tins"), sums ("1/4 cup plus 2 tbsp"), and
verbal quantities ("a pinch", "to taste"). The raw text is always kept; nothing is
converted here (conversion lives in units.py and never invents grams).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .units import Units

UNICODE_FRAC = {"½": 0.5, "⅓": 1 / 3, "⅔": 2 / 3, "¼": 0.25, "¾": 0.75, "⅕": 0.2, "⅖": 0.4,
                "⅗": 0.6, "⅘": 0.8, "⅙": 1 / 6, "⅚": 5 / 6, "⅛": 0.125, "⅜": 0.375,
                "⅝": 0.625, "⅞": 0.875}
NUM = r"(?:\d+\s+\d+/\d+|\d+\s*[½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]|\d+/\d+|\d+(?:\.\d+)?|\.\d+|[½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])"
RANGE_SEP = r"\s*(?:-|–|—|to|or)\s*"
QUALIFIERS = ("about", "approximately", "approx", "around", "roughly", "heaped", "heaping",
              "level", "scant", "generous", "packed", "rounded", "large", "small", "medium", "~")
VERBAL = ("to taste", "as needed", "as required", "as per taste", "as per requirement",
          "a pinch", "pinch", "a dash", "dash", "a handful", "handful", "a few", "few", "some",
          "a splash", "splash", "a drop", "drop", "a sprinkle", "sprinkle", "smidgen", "a smidgen")


def to_number(s: str) -> float:
    s = s.strip()
    m = re.fullmatch(r"(\d+)\s+(\d+)/(\d+)", s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / int(m.group(3))
    m = re.fullmatch(r"(\d+)\s*([½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])", s)
    if m:
        return int(m.group(1)) + UNICODE_FRAC[m.group(2)]
    if s in UNICODE_FRAC:
        return UNICODE_FRAC[s]
    m = re.fullmatch(r"(\d+)/(\d+)", s)
    if m:
        if int(m.group(2)) == 0:
            raise ValueError("zero denominator")
        return int(m.group(1)) / int(m.group(2))
    return float(s)


@dataclass
class ParsedQuantity:
    raw: str
    kind: str                       # NUMERIC | RANGE | PACKAGE | SUM | QUALITATIVE | UNPARSED
    value: Optional[float] = None
    lo: Optional[float] = None
    hi: Optional[float] = None
    unit_surface: Optional[str] = None
    unit_id: Optional[str] = None
    qualifiers: list = field(default_factory=list)
    inner: Optional["ParsedQuantity"] = None   # PACKAGE: stated content per package
    terms: list = field(default_factory=list)  # SUM: component quantities
    rest: str = ""                              # text after the quantity (usually the food)


_UNITS: Optional[Units] = None


def units() -> Units:
    global _UNITS
    if _UNITS is None:
        _UNITS = Units()
    return _UNITS


def _unit_prefix(text: str) -> tuple[Optional[str], Optional[str], str]:
    """Longest unit surface at the start of text → (surface, unit_id, remainder)."""
    t = text.lstrip()
    words = re.findall(r"[A-Za-z°][A-Za-z.°]*", t[:40])
    for n in (3, 2, 1):
        if len(words) >= n:
            cand = " ".join(words[:n])
            m = re.match(re.escape(cand) + r"\b\.?", t)
            if m:
                uid = units().lookup(cand)
                if uid:
                    return cand, uid, t[m.end():]
    m = re.match(r"(°[cfCF]|[A-Za-z]+)\b\.?", t)
    if m:
        uid = units().lookup(m.group(1))
        if uid:
            return m.group(1), uid, t[m.end():]
    return None, None, t


def parse_quantity(raw: str) -> ParsedQuantity:
    text = raw.strip()
    low = text.lower()
    for v in sorted(VERBAL, key=len, reverse=True):
        if low.startswith(v) and (len(low) == len(v) or not low[len(v)].isalpha()):
            uid = units().lookup(v.replace("a ", "", 1))
            return ParsedQuantity(raw, "QUALITATIVE", unit_surface=v,
                                  unit_id=uid or "UNIT-" + v.replace(" ", "-").replace("a-", ""),
                                  rest=text[len(v):].lstrip(" of").strip())
    quals = []
    t = text
    while True:
        m = re.match(r"\s*(" + "|".join(re.escape(q) for q in QUALIFIERS) + r")\b\.?\s*", t, re.I)
        if not m:
            break
        quals.append(m.group(1).lower())
        t = t[m.end():]
    # package: "1 (400 g) can", "2 x 400 g tins"
    m = re.match(rf"\s*({NUM})\s*\(\s*({NUM})\s*([^)]*)\)\s*(.*)", t)
    if m:
        inner = parse_quantity(f"{m.group(2)} {m.group(3)}")
        surf, uid, rest = _unit_prefix(m.group(4))
        return ParsedQuantity(raw, "PACKAGE", value=to_number(m.group(1)), unit_surface=surf,
                              unit_id=uid, qualifiers=quals, inner=inner, rest=rest.strip())
    m = re.match(rf"\s*({NUM})\s*[x×]\s*({NUM})\s*(.*)", t, re.I)
    if m:
        inner = parse_quantity(f"{m.group(2)} {m.group(3)}")
        surf, uid, _ = _unit_prefix(inner.rest)
        return ParsedQuantity(raw, "PACKAGE", value=to_number(m.group(1)), unit_surface=surf,
                              unit_id=uid, qualifiers=quals,
                              inner=ParsedQuantity(inner.raw, inner.kind, inner.value, inner.lo, inner.hi,
                                                   inner.unit_surface, inner.unit_id),
                              rest=_unit_prefix(inner.rest)[2].strip() if uid else inner.rest)
    # range
    m = re.match(rf"\s*({NUM}){RANGE_SEP}({NUM})(.*)", t, re.I)
    if m:
        lo, hi = to_number(m.group(1)), to_number(m.group(2))
        surf, uid, rest = _unit_prefix(m.group(3))
        if lo > hi:
            lo, hi = hi, lo
        return ParsedQuantity(raw, "RANGE", lo=lo, hi=hi, unit_surface=surf, unit_id=uid,
                              qualifiers=quals, rest=rest.strip())
    m = re.match(rf"\s*({NUM})(.*)", t)
    if m:
        val = to_number(m.group(1))
        surf, uid, rest = _unit_prefix(m.group(2))
        pq = ParsedQuantity(raw, "NUMERIC", value=val, unit_surface=surf, unit_id=uid,
                            qualifiers=quals, rest=rest.strip())
        mm = re.match(r"\s*(?:plus|\+|and)\s+(.*)", pq.rest, re.I)
        if mm and uid:
            second = parse_quantity(mm.group(1))
            if second.kind in ("NUMERIC", "RANGE") and second.unit_id:
                return ParsedQuantity(raw, "SUM", qualifiers=quals,
                                      terms=[ParsedQuantity(f"{m.group(1)} {surf}", "NUMERIC", value=val,
                                                            unit_surface=surf, unit_id=uid), second],
                                      rest=second.rest)
        return pq
    return ParsedQuantity(raw, "UNPARSED", qualifiers=quals, rest=t.strip())
