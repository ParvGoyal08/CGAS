r"""
K8 — re-extract literature candidates from the STORED XML (no network) with a grid-aware table
parser. Fixes two v0 extractor defects found by the AI pre-check (DEC-033):
  1. multi-level headers with colspan/rowspan were read positionally → shifted col_header;
  2. cells with trailing significance letters ("12.3 ± 0.4 (ab)", "12.3±0.4ᵃ") were dropped.
Non-detects (nd, n.d., <LOD, tr) are now kept as LEFT-censored candidates with no value.

    .venv/bin/python tools/reextract_literature_v1.py

Writes ledgers/literature/candidates_v1.csv. v0 stays frozen (pre-check records reference it);
`v0_cand_id` maps each v1 cell to its v0 row when the same physical cell was extracted before.
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/literature"
OUT = ROOT / "ledgers/literature/candidates_v1.csv"
CAPTION_CUE = re.compile(r"retention|retained|loss|cook|boil|steam|fr(y|ie)|roast|bak|microw|blanch|process|heat|thermal", re.I)
NUMTOK = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:[.,]\d+)?"
NUM = re.compile(r"^\s*(?P<lead>(?:\d(?:,\d)*\s+(?=[-~≈<>≤≥]?\d)))?(?P<cmp>[<>≤≥~≈]?)\s*(?P<v>-?(?:" + NUMTOK + r"))\s*(?P<pct1>%?)"
                 r"\s*(?:(?:±|\+/-|\+-)\s*(?P<sd>" + NUMTOK + r")\s*%?)?"
                 r"\s*(?P<flags>\(?\s*[A-Za-z*†‡§#]{0,6}(?:\s*,\s*[A-Za-z]{1,4})*\s*\)?)"
                 r"\s*(?P<word>remaining|retained|retention|loss|lost)?\s*$", re.I)
RANGE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*[–-]\s*(\d+(?:\.\d+)?)\s*%?\s*$")
ND = re.compile(r"^\s*(n\.?\s?d\.?|ND|<\s*LOD|<\s*LOQ|tr\.?|trace|BDL|bdl)\s*\d{0,2}\s*$", re.I)


def convention(cells: list[str]) -> str:
    """Decimal convention of one table: 'dot' if any point-decimal appears, 'comma' if only
    comma-decimals (1–2 or 4+ digits after the comma) appear, else 'unknown'."""
    joined = " ".join(cells)
    if re.search(r"\d\.\d", joined):
        return "dot"
    if re.search(r"\d,(\d{1,2}|\d{4,})(?!\d)", joined):
        return "comma"
    return "unknown"


def to_number(tok: str, conv: str) -> tuple[str, str]:
    """→ (normalised number string or '', flag). Never guesses an ambiguous separator."""
    if tok is None or tok == "":
        return "", ""
    if "," in tok and "." in tok:
        return tok.replace(",", ""), "THOUSANDS_SEP"
    if "," in tok:
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+", tok):
            if conv == "dot":
                return tok.replace(",", ""), "THOUSANDS_SEP"
            if conv == "comma":
                return tok.replace(",", "."), "DECIMAL_COMMA"
            return "", "AMBIGUOUS_SEPARATOR"
        return tok.replace(",", "."), "DECIMAL_COMMA"
    return tok, ""


def text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def grid(rows):
    """Expand colspan/rowspan into a rectangular grid of (text, origin_tr_position)."""
    out, pending = [], {}            # pending[(r, c)] = text carried down by rowspan
    for r, tr in enumerate(rows):
        line, c = [], 0
        cells = [x for x in tr if x.tag in ("th", "td")]
        pos = 0
        while cells or (r, c) in pending:
            if (r, c) in pending:
                line.append((pending.pop((r, c)), None))
                c += 1
                continue
            cell = cells.pop(0)
            t = text(cell)
            cs, rs = int(cell.get("colspan", 1) or 1), int(cell.get("rowspan", 1) or 1)
            for k in range(cs):
                line.append((t, pos if k == 0 else None))
                for dr in range(1, rs):
                    pending[(r + dr, c + k)] = t
            c += cs
            pos += 1
        out.append(line)
    return out


def tables(xml: bytes):
    root = ET.fromstring(xml)
    for tw in root.iter("table-wrap"):
        label = text(tw.find("label")) or tw.get("id", "")
        cap = text(tw.find("caption"))
        tb = tw.find(".//table")
        if tb is None:
            continue
        head = tb.findall("./thead/tr")
        body = tb.findall("./tbody/tr") or [tr for tr in tb.iter("tr") if tr not in head]
        yield label, cap, grid(head), grid(body), len(head)


def main() -> int:
    snaps = {}
    for line in (ROOT / "ledgers/snapshots/literature_snapshots.jsonl").read_text().splitlines():
        s = json.loads(line)
        if s.get("kind") == "fulltext":
            snaps[s["pmcid"]] = s
    v0 = {}
    with (ROOT / "ledgers/literature/candidates_v0.csv").open() as fh:
        for r in csv.DictReader(fh):
            v0[(r["pmcid"], r["table"], int(r["row_index"]), int(r["col_index"]))] = (r["cand_id"], r["cell_verbatim"], r["family"])
    fam_of = {k[0]: v[2] for k, v in v0.items()}
    rows, n = [], 0
    for path in sorted(RAW.glob("PMC*.xml")):
        pmcid = path.stem
        s = snaps.get(pmcid, {})
        for label, cap, hgrid, bgrid, nhead in tables(path.read_bytes()):
            if not CAPTION_CUE.search(cap or ""):
                continue
            width = max((len(x) for x in hgrid + bgrid), default=0)
            colhead = []
            for c in range(width):
                parts = []
                for line in hgrid:
                    t = line[c][0] if c < len(line) else ""
                    if t and (not parts or parts[-1] != t):
                        parts.append(t)
                colhead.append(" / ".join(parts))
            conv = convention([t for line in bgrid for t, _ in line[1:]])
            for ri, line in enumerate(bgrid):
                if not line:
                    continue
                row_header = line[0][0]
                for ci in range(1, len(line)):
                    t, pos = line[ci]
                    if pos is None:                      # spanned copy, not a physical cell
                        continue
                    tt = t.replace("−", "-").replace("–", "-") if t else ""
                    m = NUM.match(tt) if t else None
                    nd = ND.match(t) if t else None
                    rg = RANGE.match(t.replace("–", "-")) if (t and not m and not nd) else None
                    if not (m or nd or rg):
                        continue
                    n += 1
                    v0hit = v0.get((pmcid, label, ri, pos))
                    if nd:
                        val, sd, flags = "", "", "ND_LEFT_CENSORED"
                    elif rg:
                        val, sd, flags = "", "", f"RANGE {rg.group(1)}..{rg.group(2)}"
                    else:
                        val, f1 = to_number(m.group("v"), conv)
                        sd, f2 = to_number(m.group("sd") or "", conv)
                        fl = [m.group("cmp"), m.group("flags").strip(), f1, f2 if f2 != f1 else ""]
                        if m.group("pct1") or "%" in tt:
                            fl.append("PERCENT")
                        if m.group("word"):
                            fl.append("WORD:" + m.group("word").lower())
                        if m.group("lead"):
                            fl.append("LEADING_MARKER:" + m.group("lead").strip() + " (ambiguous: footnote or value?)")
                        flags = " ".join(x for x in fl if x)
                    rows.append({
                        "cand_id": f"LITC1-{n:06d}", "v0_cand_id": v0hit[0] if v0hit and v0hit[1] == t else "",
                        "family": fam_of.get(pmcid, ""), "pmcid": pmcid, "doi": s.get("doi") or "",
                        "licence": s.get("license", ""), "year": s.get("year", ""), "table": label, "caption": cap[:400],
                        "row_index": ri, "row_header": row_header, "grid_col": ci, "tr_position": pos,
                        "col_header": colhead[ci] if ci < len(colhead) else "", "header_levels": nhead,
                        "cell_verbatim": t, "parsed_value": val, "parsed_sd": sd, "cell_flags": flags,
                        "tier": "E5", "verification": "UNVERIFIED"})
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    mapped = sum(1 for r in rows if r["v0_cand_id"])
    nd = sum(1 for r in rows if r["cell_flags"] == "ND_LEFT_CENSORED")
    sig = sum(1 for r in rows if re.search(r"[A-Za-z]", r["cell_flags"]) and r["cell_flags"] != "ND_LEFT_CENSORED")
    print(f"v1 cells {len(rows)} (v0 had {len(v0)}); mapped to v0 {mapped}; new non-detects {nd}; with significance letters {sig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
