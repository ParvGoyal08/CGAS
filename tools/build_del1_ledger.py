r"""
K5 — build the DEL-1 evidence ledger from every acquired source.

    .venv/bin/python tools/build_del1_ledger.py

Writes ledgers/evidence/evidence_v0.jsonl (canonical, lossless), evidence_v0.parquet
(flat, for analysis) and evidence_v0.report.json. IDs are assigned per source in a
fixed order, so re-running on unchanged snapshots reproduces identical files.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from culinarystate.ingest import usda_r6  # noqa: E402

OUT = ROOT / "ledgers" / "evidence"


def flat(row) -> dict:
    d = row.model_dump(mode="json")
    conds = d.pop("conditions")
    for k, c in conds.items():
        for f, v in c.items():
            d[f"cond_{k}_{f}"] = v
    for k in ("process_ids", "process_alternatives", "study_ids", "ingredient_xrefs"):
        d[k] = "|".join(d[k])
    ver = d.pop("verification")
    d.update({f"verification_{k}": v for k, v in ver.items()})
    return d


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, rep = usda_r6.ingest(ROOT / "data/raw/usda_r6/NutrientRetention.csv", first_id=1)
    if rep["unparsed"]:
        print("UNPARSED:", rep["unparsed"])
        return 1
    with (OUT / "evidence_v0.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r.model_dump(mode="json"), sort_keys=True, ensure_ascii=False) + "\n")
    df = pd.DataFrame([flat(r) for r in rows])
    df.to_parquet(OUT / "evidence_v0.parquet", index=False)
    sha = hashlib.sha256((OUT / "evidence_v0.jsonl").read_bytes()).hexdigest()
    report = {
        "ledger_version": "v0", "sha256_jsonl": sha, "rows": len(rows),
        "by_source": {"SRC-0001 USDA-R6": len(rows)},
        "usda_r6": {k: v for k, v in rep.items() if k != "unparsed"},
        "evaluable_rows": sum(r.evaluable for r in rows),
        "distinct_ingredients": df["ingredient_id"].nunique(),
        "distinct_targets": df["target_variable"].nunique(),
        "rows_with_time_condition": int(df.get("cond_t_status").notna().sum()) if "cond_t_status" in df else 0,
    }
    (OUT / "evidence_v0.report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
