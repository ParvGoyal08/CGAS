r"""
K8 / T05 — literature search round 2 (red meat, poultry, legumes): ACQUISITION ONLY.
    .venv/bin/python tools/fetch_literature_round2.py [per_family]
Stores licence-ok (CC BY / CC BY-SA / CC0) primary-study full texts that contain ≥1 table; logs every
query and its hit counts (ledgers/literature/search_log_r2.jsonl); appends SNAP records. Extraction is a
separate step (tools/reextract_literature_v1.py --all-tables --only …). Crawl-Delay 10 s (ebi.ac.uk).
Reviews are excluded (primary controlled studies prioritised). H2: open-access papers approved (DEC-019).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
import time
from datetime import datetime, timezone

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/literature"
SNAP = ROOT / "ledgers/snapshots/literature_snapshots.jsonl"
LOG = ROOT / "ledgers/literature/search_log_r2.jsonl"
API = "https://www.ebi.ac.uk/europepmc/webservices/rest"
UA = {"User-Agent": "CulinaryState-research/0.1 (IIIT-Delhi course project; contact planininterns@gmail.com)"}
OK = {"cc by", "cc0", "cc by-sa"}
PROC = '(cooking OR cooked OR boiling OR boiled OR frying OR fried OR roasting OR roasted OR grilling OR grilled OR baking OR stewing OR "sous vide" OR "pressure cooking" OR microwave OR steaming OR braising OR soaking)'
EFFECT = '(retention OR loss OR losses OR reduction OR "true retention" OR "effect of cooking")'
FAMILIES = {
    "red_meat": '(beef OR pork OR lamb OR mutton OR veal OR "red meat")',
    "poultry": '(chicken OR poultry OR turkey OR "broiler meat")',
    "legume": '(lentil OR lentils OR chickpea OR chickpeas OR "common bean" OR beans OR pulses OR legume OR legumes OR "faba bean" OR cowpea)',
}
TARGETS = '(vitamin OR vitamins OR thiamin OR riboflavin OR niacin OR folate OR "vitamin B" OR mineral OR minerals OR iron OR zinc OR selenium OR "fatty acid" OR polyphenol OR phenolic OR phytate OR carotenoid OR tocopherol)'


def get(url, **params):
    time.sleep(10)
    r = requests.get(url, params=params or None, headers=UA, timeout=120)
    return r, {"url": r.url, "status": r.status_code, "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "sha256": hashlib.sha256(r.content).hexdigest(), "bytes": len(r.content)}


def main() -> int:
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    have = {p.stem for p in RAW.glob("PMC*.xml")}
    for fam, terms in FAMILIES.items():
        q = (f"(TITLE:{terms} OR ABSTRACT:{terms}) AND (TITLE:{PROC} OR ABSTRACT:{PROC}) AND (ABSTRACT:{EFFECT} OR TITLE:{EFFECT}) "
             f"AND (ABSTRACT:{TARGETS} OR TITLE:{TARGETS}) AND OPEN_ACCESS:y AND HAS_FT:y NOT PUB_TYPE:\"review\" NOT TITLE:review")
        r, rec = get(f"{API}/search", query=q, format="json", pageSize=60, resultType="core")
        hits = r.json()["resultList"]["result"] if r.status_code == 200 else []
        ok = [x for x in hits if x.get("pmcid") and (x.get("license") or "").lower() in OK and x["pmcid"] not in have]
        log = {"round": "R2", "family": fam, "query": q, "utc": rec["retrieved_utc"], "status": r.status_code,
               "hit_count": r.json().get("hitCount") if r.status_code == 200 else None, "returned": len(hits),
               "licence_ok_new": len(ok), "stored": []}
        for x in ok:
            if len(log["stored"]) >= per:
                break
            fr, frec = get(f"{API}/{x['pmcid']}/fullTextXML")
            if fr.status_code != 200 or b"<table" not in fr.content:
                continue
            (RAW / f"{x['pmcid']}.xml").write_bytes(fr.content)
            have.add(x["pmcid"])
            with SNAP.open("a") as fh:
                fh.write(json.dumps({**frec, "kind": "fulltext", "round": "R2", "family": fam, "pmcid": x["pmcid"],
                                     "license": x.get("license"), "doi": x.get("doi"), "title": x.get("title"),
                                     "year": x.get("pubYear"), "query_family": fam}) + "\n")
            log["stored"].append({"pmcid": x["pmcid"], "title": re.sub(r"<[^>]+>", "", x.get("title", ""))[:160],
                                  "year": x.get("pubYear"), "license": x.get("license")})
            print(fam, x["pmcid"], x.get("license"), flush=True)
        with LOG.open("a") as fh:
            fh.write(json.dumps(log) + "\n")
        print(fam, "hits", log["hit_count"], "licence-ok new", log["licence_ok_new"], "stored", len(log["stored"]), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
