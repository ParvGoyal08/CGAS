r"""
D1 / T04 — promote HUMAN-VERIFIED literature cells into EvidenceRows (tier E2/E4, VERIFIED).
    .venv/bin/python tools/promote_literature.py [--queue Q] [--out DIR]

A queue row is promoted only if a human signed it: is_retention_relevant == "yes", verifier and verified_utc set.
The verifier may CORRECT the AI pre-check by filling final_* columns (final_ingredient_id, final_process_ids,
final_target, final_value_kind, final_unit, final_tier, final_conditions); a blank final_* = AI suggestion accepted.
Values come ONLY from the verbatim cell (parsed_value, re-checked against cell_verbatim). A processed concentration
with a same-unit raw counterpart additionally yields a DERIVED apparent-retention row (processed/raw x 100), logged
with both cell ids. Rows that cannot be promoted (unmapped process, missing unit, value not in the cell) go to
promotion_rejects.csv with the reason — nothing is guessed. IDs (EVD-/SRC-/STUDY-) come from an append-only map
(ledgers/literature/id_map.csv): re-running never renumbers.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from culinarystate.ledger.schema import EvidenceRow  # noqa: E402

PROCS = {r["proc_id"] for r in csv.DictReader((ROOT / "ledgers/process/proc_v0.csv").open())}
COND_RX = re.compile(r"^\s*(?:PROC-[a-z0-9-]+:)?(T|t|pH|aw|moisture|pressure|medium|water_handling)\s*=\s*(.+?)\s*\((MEASURED|RANGE|QUALITATIVE)\)\s*$")
UNIT_MAP = {"c": "degC", "°c": "degC", "degc": "degC", "min": "min", "mins": "min", "minute": "min", "minutes": "min",
            "h": "h", "hr": "h", "hours": "h", "s": "s", "sec": "s", "kpa": "kPa", "bar": "bar", "%": "%"}


class IdMap:
    def __init__(self, path: pathlib.Path):
        self.path, self.m = path, {}
        if path.exists():
            for r in csv.DictReader(path.open()):
                self.m[(r["kind"], r["key"])] = r["id"]

    def get(self, kind: str, key: str, fmt: str, start: int) -> str:
        if (kind, key) not in self.m:
            n = start + sum(1 for k, _ in self.m if k == kind)
            self.m[(kind, key)] = fmt.format(n)
        return self.m[(kind, key)]

    def save(self):
        with self.path.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["kind", "key", "id"])
            for (k, key), i in sorted(self.m.items(), key=lambda x: (x[0][0], x[1])):
                w.writerow([k, key, i])


def conditions(text: str) -> dict:
    out = {}
    for part in filter(None, (p.strip() for p in (text or "").split(";"))):
        m = COND_RX.match(part)
        if not m:
            continue
        key, val, status = m.groups()
        if status == "QUALITATIVE" or key in ("medium", "water_handling"):
            out[key] = {"status": "QUALITATIVE", "raw": val}
            continue
        num = re.match(r"^([0-9.]+)\s*(?:[-–]\s*([0-9.]+))?\s*([A-Za-z°%]+)?", val)
        if not num:
            out[key] = {"status": "QUALITATIVE", "raw": val}
            continue
        unit = UNIT_MAP.get((num.group(3) or "").lower(), num.group(3))
        if num.group(2):
            out[key] = {"status": "RANGE", "lo": float(num.group(1)), "hi": float(num.group(2)), "unit": unit, "raw": val}
        elif unit:
            out[key] = {"status": "MEASURED", "value": float(num.group(1)), "unit": unit, "raw": val}
        else:
            out[key] = {"status": "QUALITATIVE", "raw": val}
    return out


def pick(r, k):
    return (r.get(f"final_{k}") or "").strip() or (r.get(f"ai_{k}") or "").strip()


def value_in_cell(v: str, cell: str) -> bool:
    if not v:
        return False
    digits = re.sub(r"[^0-9.]", "", cell.replace(",", ""))
    return v.replace(".0", "").rstrip("0").rstrip(".") in digits or v in cell.replace(",", "")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", default=str(ROOT / "ledgers/literature/verification_queue_ranked_v1.csv"))
    ap.add_argument("--out", default=str(ROOT / "ledgers/evidence"))
    ap.add_argument("--id-map", default=str(ROOT / "ledgers/literature/id_map.csv"))
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(a.queue, encoding="utf-8")))
    by_id = {}                                              # counterpart lookup: extraction values + any pre-check row
    for f in ("candidates_v1.csv", "candidates_r2.csv", "rejected_candidates.csv"):
        fp = ROOT / "ledgers/literature" / f
        if fp.exists():
            for c in csv.DictReader(fp.open(encoding="utf-8")):
                by_id.setdefault(c["cand_id"], {}).update({k: v for k, v in c.items() if v})
    for r in rows:
        by_id.setdefault(r["cand_id"], {}).update({k: v for k, v in r.items() if v})
    snaps = {}
    for line in (ROOT / "ledgers/snapshots/literature_snapshots.jsonl").read_text().splitlines():
        s = json.loads(line)
        if s.get("kind") == "fulltext" and s.get("status", 200) == 200:
            snaps[s["pmcid"]] = s
    ids = IdMap(pathlib.Path(a.id_map))
    ev, rejects = [], []
    signed = [r for r in rows if r.get("is_retention_relevant") == "yes" and r.get("verifier") and r.get("verified_utc")]
    for r in signed:
        why = []
        procs = [p.strip() for p in pick(r, "process_ids").split(";") if p.strip()]
        if not procs or any(p not in PROCS for p in procs):
            why.append(f"process not mapped to PROC-: {procs}")
        unit = pick(r, "unit")
        if not unit:
            why.append("no unit")
        v = r.get("parsed_value", "")
        if not value_in_cell(v, r["cell_verbatim"]):
            why.append(f"parsed value {v!r} not found in cell {r['cell_verbatim']!r}")
        ing = pick(r, "ingredient_id").lower()
        if not re.fullmatch(r"ING-[a-z0-9]+(-[a-z0-9]+)*", ing.replace("ing-", "ING-", 1)):
            why.append(f"bad ingredient id {ing!r}")
        if why:
            rejects.append({"cand_id": r["cand_id"], "reason": "; ".join(why)})
            continue
        pm = r["pmcid"]
        src = ids.get("SRC", pm, "SRC-{:04d}", 2001)
        study = ids.get("STUDY", pm, "STUDY-{:06d}", 1)
        snap = snaps.get(pm, {})
        tier = (r.get("final_tier") or r.get("proposed_tier") or "E4").strip()
        locator = f"{pm} {r['table']} row {r.get('row_header', '')!r} col {r.get('col_header', '')!r}"
        vk = pick(r, "value_kind") or "CONCENTRATION"
        common = dict(source_id=src, source_family_id=pm, origin_type="REVIEW_AGGREGATE" if r.get("secondary") == "True" else "PRIMARY_STUDY",
                      study_ids=(study,), source_record=f"{locator}; cell {r['cand_id']}; sha256 {snap.get('sha256', 'UNKNOWN')}",
                      ingredient_raw=r.get("ai_food") or ing, ingredient_id=ing.replace("ing-", "ING-", 1),
                      process_raw=r.get("ai_process_text") or ";".join(procs), process_ids=tuple(procs),
                      conditions={k: v for k, v in conditions(pick(r, "conditions")).items()},
                      target_type="OTHER", target_variable=pick(r, "target"),
                      retention_method={"TRUE_RETENTION": "TRUE_RETENTION", "APPARENT_RETENTION": "APPARENT_RETENTION"}.get(
                          r.get("table_retention_method", ""), "UNSPECIFIED"),
                      basis=r.get("table_basis") if r.get("table_basis") in ("WET", "DRY") else "UNSPECIFIED",
                      tier=tier, ledger_version="v1",
                      verification={"status": "VERIFIED", "verifier": r["verifier"], "span_locator": locator})
        sd = r.get("parsed_sd") or None
        base = {**common, "evidence_id": ids.get("EVD", r["cand_id"], "EVD-{:06d}", 100001), "value_kind": vk,
                "value": float(v), "unit": unit, "sd": float(sd) if sd else None, "provenance": "EXPLICIT_SOURCE",
                "notes": f"verified {r['verified_utc']}; AI pre-check fields reviewed by {r['verifier']}"}
        try:
            ev.append(EvidenceRow(**base))
        except Exception as e:  # schema violation → reject with the message
            rejects.append({"cand_id": r["cand_id"], "reason": f"schema: {str(e).splitlines()[0]}"})
            continue
        raw = by_id.get(r.get("raw_counterpart_cand_id") or "")
        if (r.get("ai_role") == "PROCESSED_VALUE" and vk == "CONCENTRATION" and raw and raw.get("parsed_value")
                and (raw.get("ai_unit") or unit) == unit and float(raw["parsed_value"]) > 0):
            ret = float(v) / float(raw["parsed_value"]) * 100       # APPARENT retention; both cells logged below
            ev.append(EvidenceRow(**{**common, "evidence_id": ids.get("EVD", r["cand_id"] + "#derived", "EVD-{:06d}", 100001),
                                     "value_kind": "RETENTION_PERCENT", "value": round(ret, 4), "unit": "%",
                                     "retention_method": "APPARENT_RETENTION", "provenance": "DERIVED_DETERMINISTIC",
                                     "notes": f"DERIVED: {r['cand_id']} / {r['raw_counterpart_cand_id']} x 100 "
                                              f"({r['cell_verbatim']!r} / {raw.get('cell_verbatim', '')!r}); verified by {r['verifier']}"}))
    ids.save()
    (out / "literature_v1.jsonl").write_text("".join(e.model_dump_json() + "\n" for e in ev))
    with (out / "literature_v1.rejects.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["cand_id", "reason"])
        w.writeheader()
        w.writerows(rejects)
    rep = {"signed_rows": len(signed), "evidence_rows": len(ev), "derived_rows": sum("DERIVED:" in (e.notes or "") for e in ev),
           "rejected": len(rejects), "studies": len({e.study_ids[0] for e in ev}), "meets_DEL1_40": len(
               [e for e in ev if e.provenance.value == "EXPLICIT_SOURCE"]) >= 40}
    (out / "literature_v1.report.json").write_text(json.dumps(rep, indent=1))
    print(rep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
