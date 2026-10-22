r"""
T02 — merge the AI pre-check (ledgers/literature/ai_precheck/*.jsonl) into
  ledgers/literature/ai_precheck_v0.csv      every pre-checked cell, joined to candidates v0 + v1
  ledgers/literature/verification_sheet_v1.csv   the ranked sheet for HUMAN final verification

    .venv/bin/python tools/merge_ai_precheck.py

Deterministic checks (a record failing any is excluded and reported, never repaired):
  cand_id exists in candidates_v0; quotes are verbatim substrings of the paper XML (whitespace-
  normalised); every PROC- id exists in proc_v0 (or PROC-UNMAPPED:<verb>); the AI wrote no numbers
  (values come only from cell_verbatim). Headers shown to the human come from the grid-aware v1
  extraction (DEC-033), because v0 headers can be shifted.

Sheet ranking: RETENTION_REPORTED before PROCESSED_VALUE; confidence high > medium; round-robin over
anchor families; at most 8 cells per paper among the first 60. Low-confidence cells are kept in the
merged file but left out of the sheet.
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
from collections import defaultdict, deque

import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIT = ROOT / "ledgers/literature"
HUMAN = ["is_retention_relevant", "verifier", "verified_utc", "human_notes"]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def main() -> int:
    v0 = {r["cand_id"]: r for r in csv.DictReader((LIT / "candidates_v0.csv").open())}
    v1_by_v0 = {r["v0_cand_id"]: r for r in csv.DictReader((LIT / "candidates_v1.csv").open()) if r["v0_cand_id"]}
    procs = {r["proc_id"] for r in csv.DictReader((ROOT / "ledgers/process/proc_v0.csv").open())}
    xml_text = {}
    tables, cells, bad = {}, [], defaultdict(list)
    for f in sorted((LIT / "ai_precheck").glob("PMC*.jsonl")):
        pmcid = f.stem
        if pmcid not in xml_text:
            xml_text[pmcid] = norm("".join(ET.parse(ROOT / f"data/raw/literature/{pmcid}.xml").getroot().itertext()))
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("type") == "table":
                tables[(pmcid, r["table"])] = r
            elif r.get("type") == "cell":
                cells.append(r)
    out = []
    for r in cells:
        cid, pmcid = r["cand_id"], r["pmcid"]
        why = []
        if cid not in v0:
            why.append("unknown cand_id")
        for q in ("ai_quote",):
            if r.get(q) and norm(r[q]) not in xml_text[pmcid]:
                why.append(f"{q} not verbatim")
        for p in filter(None, (r.get("ai_process_ids") or "").split(";")):
            p = p.split(":")[0] if p.startswith("PROC-UNMAPPED") else p.strip()
            if p != "PROC-UNMAPPED" and p not in procs:
                why.append(f"unknown {p}")
        if any(k in r for k in ("value", "ai_value", "parsed_value")):
            why.append("AI wrote a value field")
        if why:
            bad[pmcid].append((cid, why))
            continue
        c0, c1 = v0[cid], v1_by_v0.get(cid, {})
        t = tables.get((pmcid, r["table"]), {})
        raw = v0.get(r.get("ai_raw_counterpart_cand_id") or "", {})
        out.append({
            "cand_id": cid, "cand_id_v1": c1.get("cand_id", ""), "family": c0["family"], "pmcid": pmcid,
            "doi": c0["doi"], "table": r["table"], "row_header": c1.get("row_header", c0["row_header"]),
            "col_header": c1.get("col_header", c0["col_header"]), "cell_verbatim": c0["cell_verbatim"],
            "raw_counterpart_cand_id": r.get("ai_raw_counterpart_cand_id", ""),
            "raw_counterpart_verbatim": raw.get("cell_verbatim", ""),
            **{k: (";".join(r[k]) if isinstance(r.get(k), list) else r.get(k, "")) for k in (
                "ai_relevant", "ai_role", "ai_food", "ai_ingredient_id", "ai_process_text", "ai_process_ids",
                "ai_conditions", "ai_target", "ai_value_kind", "ai_unit", "ai_flags", "ai_confidence", "ai_quote")},
            "table_basis": t.get("basis", ""), "table_retention_method": t.get("retention_method", ""),
            "table_methods_quote": t.get("methods_quote", ""), "provenance": "AI_PRECHECK",
            "paper_url": f"https://europepmc.org/article/PMC/{pmcid}"})
    keys = list(out[0]) if out else []
    with (LIT / "ai_precheck_v0.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(out)
    # ---- ranked human sheet
    pri = {"RETENTION_REPORTED": 0, "PROCESSED_VALUE": 1}
    conf = {"high": 0, "medium": 1}
    good = [r for r in out if r["ai_relevant"] == "yes" and r["ai_role"] in pri and r["ai_confidence"] in conf]
    good.sort(key=lambda r: (pri[r["ai_role"]], conf[r["ai_confidence"]], r["pmcid"], r["cand_id"]))
    by_fam = defaultdict(list)
    for r in good:
        by_fam[r["family"]].append(r)
    sheet, per_paper, taken = [], defaultdict(int), set()
    fams = deque(sorted(by_fam))
    while len(sheet) < 60 and fams:                         # head: round-robin, <= 8 per paper
        f = fams.popleft()
        pick = next((r for r in by_fam[f] if r["cand_id"] not in taken and per_paper[r["pmcid"]] < 8), None)
        if pick is None:
            continue                                         # family exhausted under the cap
        sheet.append(pick)
        taken.add(pick["cand_id"])
        per_paper[pick["pmcid"]] += 1
        fams.append(f)
    sheet += [r for r in good if r["cand_id"] not in taken]  # tail: everything else, in priority order
    with (LIT / "verification_sheet_v1.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["sheet_rank"] + keys + HUMAN)
        w.writeheader()
        for i, r in enumerate(sheet, 1):
            w.writerow({"sheet_rank": i, **r, **{h: "" for h in HUMAN}})
    n_tab = sum(1 for t in tables.values() if t.get("verdict") == "PROCESS_EFFECT_TABLE")
    print(f"papers pre-checked {len({k[0] for k in tables})}; tables {len(tables)} (process-effect {n_tab}); "
          f"cell records {len(cells)}; accepted {len(out)}; rejected {sum(len(v) for v in bad.values())}")
    print(f"relevant yes: {sum(r['ai_relevant'] == 'yes' for r in out)} "
          f"(high {sum(r['ai_relevant'] == 'yes' and r['ai_confidence'] == 'high' for r in out)}, "
          f"medium {sum(r['ai_relevant'] == 'yes' and r['ai_confidence'] == 'medium' for r in out)}); "
          f"sheet rows {len(sheet)} from {len({r['pmcid'] for r in sheet})} papers, {len({r['family'] for r in sheet})} families")
    for p, v in bad.items():
        print("rejected", p, v[:3])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
