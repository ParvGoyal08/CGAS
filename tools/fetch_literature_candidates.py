r"""
K8 — literature CANDIDATE rows from open-access papers (H2 approved 2026-10-08, DEC-019).

    .venv/bin/python tools/fetch_literature_candidates.py [per_family]

For each of the 12 v4.0 AI5 anchor families: one Europe PMC search (title must name a cooking
process AND retention/loss/effect), keep papers whose licence permits storage (CC BY, CC BY-SA,
CC0), fetch the JATS full text, and copy every table cell VERBATIM with its exact location
(PMCID, table label, row header, column header).

Nothing here is evidence yet: every candidate is tier E5, verification UNVERIFIED, and the
mapping fields (ingredient, process, conditions, target, basis, retention method) are left
empty for a human verifier (docs/annotation/literature_verification_v0.md). Values are never
inferred by the machine. Crawl-Delay 10 s honoured (ebi.ac.uk robots.txt).
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/literature"
SNAP = ROOT / "ledgers/snapshots/literature_snapshots.jsonl"
OUT = ROOT / "ledgers/literature/candidates_v0.csv"
API = "https://www.ebi.ac.uk/europepmc/webservices/rest"
UA = {"User-Agent": "CulinaryState-research/0.1 (IIIT-Delhi course project; contact planininterns@gmail.com)"}
DELAY = 10.0
OK_LICENCES = {"cc by", "cc0", "cc by-sa"}

PROC = "(cooking OR cooked OR boiling OR boiled OR steaming OR steamed OR frying OR fried OR roasting OR baking OR microwave OR blanching OR \"thermal processing\" OR \"domestic processing\")"
EFFECT = "(retention OR loss OR losses OR degradation OR \"effect of\" OR changes)"
FAMILIES = {
    "allium": "(onion OR garlic OR leek OR allium)",
    "leafy_green": "(spinach OR kale OR cabbage OR \"leafy vegetables\" OR amaranth OR broccoli)",
    "tuber": "(potato OR potatoes OR cassava OR yam OR \"sweet potato\")",
    "grain_starch": "(rice OR wheat OR pasta OR maize OR millet OR cereal)",
    "legume": "(bean OR beans OR lentil OR chickpea OR legume OR legumes OR pulses)",
    "fruit": "(tomato OR fruit OR apple OR berries OR mango)",
    "dairy_emulsion": "(milk OR cheese OR dairy OR butter OR yogurt)",
    "egg_protein": "(egg OR eggs OR tofu)",
    "red_meat": "(beef OR pork OR lamb OR mutton OR meat)",
    "poultry": "(chicken OR poultry OR turkey)",
    "oil_frying_medium": "(\"frying oil\" OR \"vegetable oil\" OR \"deep-frying\" OR \"deep frying\")",
    "fermented": "(fermented OR fermentation OR kimchi OR sauerkraut OR idli OR dosa)",
}
CAPTION_CUE = re.compile(r"retention|retained|loss|cook|boil|steam|fr(y|ie)|roast|bak|microw|blanch|process|heat|thermal", re.I)


def get(url, **params):
    time.sleep(DELAY)
    r = requests.get(url, params=params or None, headers=UA, timeout=120)
    rec = {"url": r.url, "status": r.status_code, "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "sha256": hashlib.sha256(r.content).hexdigest(), "bytes": len(r.content)}
    return r, rec


def text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def tables(xml: bytes):
    root = ET.fromstring(xml)
    for tw in root.iter("table-wrap"):
        label = text(tw.find("label")) or tw.get("id", "")
        cap = text(tw.find("caption"))
        tb = tw.find(".//table")
        if tb is None:
            continue
        head_rows = tb.findall("./thead/tr")
        col_names = []
        if head_rows:
            col_names = [text(c) for c in head_rows[-1] if c.tag in ("th", "td")]
        body = tb.findall("./tbody/tr") or [tr for tr in tb.iter("tr") if tr not in head_rows]
        yield label, cap, col_names, [[text(c) for c in tr if c.tag in ("th", "td")] for tr in body]


NUM = re.compile(r"^\s*([<>≤≥]?)\s*(-?\d+(?:[.,]\d+)?)\s*(?:(?:±|\+/-|\+-)\s*(\d+(?:[.,]\d+)?))?\s*([a-zA-Z*†‡§]*)\s*$")


def main() -> int:
    per_family = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    snaps, rows, seen = [], [], set()
    for fam, terms in FAMILIES.items():
        q = f"TITLE:{PROC} AND TITLE:{EFFECT} AND (TITLE:{terms} OR ABSTRACT:{terms}) AND OPEN_ACCESS:y AND HAS_FT:y"
        r, rec = get(f"{API}/search", query=q, format="json", pageSize=25, resultType="core")
        snaps.append({**rec, "kind": "search", "family": fam})
        if r.status_code != 200:
            print(fam, "search failed", r.status_code, flush=True)
            continue
        hits = [x for x in r.json()["resultList"]["result"]
                if x.get("pmcid") and (x.get("license") or "").lower() in OK_LICENCES and x["pmcid"] not in seen]
        print(fam, "hits", r.json().get("hitCount"), "licence-ok", len(hits), flush=True)
        taken = 0
        for x in hits:
            if taken >= per_family:
                break
            pmcid = x["pmcid"]
            fr, frec = get(f"{API}/{pmcid}/fullTextXML")
            snaps.append({**frec, "kind": "fulltext", "family": fam, "pmcid": pmcid, "license": x.get("license"),
                          "doi": x.get("doi"), "title": x.get("title"), "year": x.get("pubYear")})
            if fr.status_code != 200:
                continue
            try:
                tbs = list(tables(fr.content))
            except ET.ParseError:
                continue
            useful = [t for t in tbs if CAPTION_CUE.search(t[1] or "")]
            if not useful:
                continue
            (RAW / f"{pmcid}.xml").write_bytes(fr.content)
            seen.add(pmcid)
            taken += 1
            for label, cap, cols, body in useful:
                for ri, cells in enumerate(body):
                    if not cells:
                        continue
                    for ci, cell in enumerate(cells[1:], start=1):
                        m = NUM.match(cell.replace("−", "-"))
                        if not m:
                            continue
                        rows.append({
                            "cand_id": f"LITC-{len(rows) + 1:06d}", "family": fam, "pmcid": pmcid, "doi": x.get("doi") or "",
                            "licence": x.get("license"), "year": x.get("pubYear"), "table": label, "caption": cap[:400],
                            "row_index": ri, "row_header": cells[0], "col_index": ci,
                            "col_header": cols[ci] if ci < len(cols) else "", "cell_verbatim": cell,
                            "parsed_value": m.group(2).replace(",", "."), "parsed_sd": (m.group(3) or "").replace(",", "."),
                            "cell_flags": (m.group(1) + m.group(4)).strip(),
                            "tier": "E5", "verification": "UNVERIFIED",
                            # filled by the human verifier only:
                            "is_retention_relevant": "", "ingredient_id": "", "process_ids": "", "conditions": "",
                            "target": "", "value_kind": "", "basis": "", "retention_method": "", "verifier": "", "verified_utc": ""})
            print("  ", pmcid, x.get("license"), "tables", len(useful), "cells so far", len(rows), flush=True)
    with SNAP.open("a") as fh:
        for s in snaps:
            fh.write(json.dumps(s) + "\n")
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("papers", len(seen), "candidate cells", len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
