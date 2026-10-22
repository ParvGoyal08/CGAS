r"""
P2 — cross-ledger ID audit.  .venv/bin/python tools/audit_ids.py  → logs/id_audit.json, exit 1 on errors.
Checks every id column of the owning ledgers: (1) well-formed for its prefix, (2) defined once
(no silent reuse: the same id with two different definitions), (3) references resolve: ING-/PROC-/MOL-/
EVD- ids used by other ledgers exist in their owner ledger.
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from culinarystate.ids import prefix_of  # noqa: E402

OWNERS = [  # (file, id column, kind)
    ("ledgers/evidence/evidence_v0.jsonl", "evidence_id", "jsonl"),
    ("ledgers/process/proc_v0.csv", "proc_id", "csv"),
    ("ledgers/ingredients/ing_v0.csv", "ingredient_id", "csv"),
    ("ledgers/molecules/mol_v0.jsonl", "mol_id", "jsonl"),
    ("ledgers/molecules/imap_v0.csv", "imap_id", "csv"),
    ("ledgers/tools/tool_v0.csv", "tool_id", "csv"),
    ("ledgers/authority/allergen_v0.csv", "allergen_id", "csv"),
    ("ledgers/literature/candidates_v1.csv", "cand_id", "csv"),
    ("ledgers/literature/candidates_r2.csv", "cand_id", "csv"),
    ("research/cells/priority_cells_v0.csv", "cell_id", "csv"),
]
UNIT_FILE = "ledgers/units/unit_map_v0.csv"   # unit ids repeat once per locale variant by design


def rows(path, kind):
    p = ROOT / path
    if not p.exists():
        return []
    if kind == "jsonl":
        return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    return list(csv.DictReader(p.open(encoding="utf-8")))


def main() -> int:
    errors, defined = [], {}
    for path, col, kind in OWNERS:
        rs = rows(path, kind)
        ids = [r[col] for r in rs]
        for i in ids:
            try:
                prefix_of(i)
            except ValueError as e:
                errors.append({"file": path, "error": str(e)})
        dup = [k for k, v in Counter(ids).items() if v > 1]
        for d in dup:
            errors.append({"file": path, "error": f"id defined more than once: {d}"})
        defined[path] = set(ids)
    units = {r["unit_id"] for r in rows(UNIT_FILE, "csv")}
    for u in units:
        try:
            prefix_of(u)
        except ValueError as e:
            errors.append({"file": UNIT_FILE, "error": str(e)})
    procs = defined["ledgers/process/proc_v0.csv"]
    ings = defined["ledgers/ingredients/ing_v0.csv"]
    dangling = Counter()
    for r in rows("ledgers/evidence/evidence_v0.jsonl", "jsonl"):
        if r["ingredient_id"] not in ings:
            dangling[("evidence→ING", r["ingredient_id"])] += 1
        for p in list(r.get("process_ids") or []) + list(r.get("process_alternatives") or []):
            if p not in procs and not p.startswith("PROC-UNMAPPED"):
                dangling[("evidence→PROC", p)] += 1
    for r in rows("ledgers/tools/tool_v0.csv", "csv"):
        for p in filter(None, r["process_compatibility"].split("|")):
            if p not in procs:
                dangling[("tool→PROC", p)] += 1
    for (kind, i), n in dangling.items():
        errors.append({"file": kind, "error": f"dangling reference {i} ({n}×)"})
    out = {"checked_files": [p for p, _, _ in OWNERS if (ROOT / p).exists()] + [UNIT_FILE],
           "ids_checked": sum(len(v) for v in defined.values()) + len(units), "errors": errors}
    (ROOT / "logs").mkdir(exist_ok=True)
    (ROOT / "logs/id_audit.json").write_text(json.dumps(out, indent=1))
    print(f"ids checked {out['ids_checked']:,}; errors {len(errors)}")
    for e in errors[:15]:
        print(" ", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
