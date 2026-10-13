r"""
P14 — one reusable data-report generator for every ledger.
    .venv/bin/python tools/data_report.py <plugin> [--out eda/<plugin>/auto]
    .venv/bin/python tools/data_report.py --all            (→ eda/global/auto/summary.json + index.md)
Core profile for any table: sha256, rows, exact/key duplicates, missingness (UNKNOWN counted separately from empty),
long tail (top-10% share), source / licence / provenance / tier distributions, condition completeness, validation
failures, unresolved mappings, split leakage. A plugin only says how to load its data and which columns play which
role; a plugin whose input is missing reports 'not available' instead of failing.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
UNKNOWN_TOKENS = {"UNKNOWN", "UNSPECIFIED", "UNVERIFIED", "NOT_APPLICABLE"}


@dataclass
class Plugin:
    name: str
    paths: list
    load: Callable[[list], pd.DataFrame]
    key: Optional[str] = None
    freq: Optional[str] = None                     # column whose value counts form the long tail
    roles: dict = field(default_factory=dict)      # role → column (source, licence, provenance, tier, split)
    validate: Optional[Callable[[pd.DataFrame], list]] = None
    unresolved: Optional[Callable[[pd.DataFrame], int]] = None
    conditions: Optional[Callable[[pd.DataFrame], dict]] = None


def _csv(paths):
    return pd.concat([pd.read_csv(ROOT / p, keep_default_na=False, dtype=str) for p in paths if (ROOT / p).exists()],
                     ignore_index=True)


def _jsonl(paths):
    rows = [json.loads(x) for p in paths if (ROOT / p).exists() for x in (ROOT / p).read_text().splitlines() if x.strip()]
    return pd.json_normalize(rows, max_level=1)


def _evidence_validate(df):
    from culinarystate.ledger.schema import EvidenceRow
    bad = []
    for p in ("ledgers/evidence/evidence_v0.jsonl", "ledgers/evidence/literature_v1.jsonl"):
        f = ROOT / p
        if f.exists():
            for i, x in enumerate(f.read_text().splitlines()):
                try:
                    EvidenceRow.model_validate_json(x)
                except Exception as e:  # noqa: BLE001
                    bad.append(f"{p}:{i + 1}: {str(e).splitlines()[0]}")
    return bad


def _evidence_conditions(df):
    out = {}
    for ax in ("T", "t", "pH", "aw", "moisture", "pressure", "medium", "water_handling"):
        col = f"conditions.{ax}"
        if col in df:
            st = df[col].map(lambda c: c.get("status") if isinstance(c, dict) else None)
            out[ax] = float((st.notna() & (st != "UNKNOWN")).mean())
        else:
            out[ax] = 0.0
    return out


def _gold_load(paths):
    from tools.validate_gold import check
    rows = [{"file": str(f.relative_to(ROOT)), "valid": check(f)[0], "expected_invalid": "invalid" in f.parts}
            for p in paths for f in sorted((ROOT / p).rglob("*.yaml"))]
    return pd.DataFrame(rows)


def _benchmark_load(paths):
    import yaml
    rows = []
    for p in paths:
        for f in sorted((ROOT / p).glob("*.yaml")):
            for it in yaml.safe_load(f.read_text()) or []:
                rows.append({k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in it.items()} | {"_file": f.name})
    return pd.DataFrame(rows)


def _transition_load(paths):
    rows = []
    for p in paths:
        for m in sorted((ROOT / p).glob("*/verdicts.json")):
            v = json.loads(m.read_text())
            rows.append({"run": m.parent.name, "H2_D5": v.get("H2_D5", {}).get("verdict"),
                         "D7": v.get("D7_promotion", {}).get("verdict"), "neg_control": v.get("negative_control", {}).get("verdict")})
    return pd.DataFrame(rows)


PLUGINS = {p.name: p for p in [
    Plugin("evidence", ["ledgers/evidence/evidence_v0.jsonl", "ledgers/evidence/literature_v1.jsonl"], _jsonl,
           key="evidence_id", freq="ingredient_id",
           roles={"source": "source_id", "provenance": "provenance", "tier": "tier", "origin": "origin_type"},
           validate=_evidence_validate, conditions=_evidence_conditions,
           unresolved=lambda d: int((d.get("ingredient_link_status", pd.Series(dtype=str)) == "UNRESOLVED_EXTERNAL").sum())),
    Plugin("literature", ["ledgers/literature/verification_queue_ranked_v1.csv"], _csv, key="cand_id", freq="family",
           roles={"source": "pmcid", "category": "queue_category", "tier": "proposed_tier", "confidence": "ai_confidence"},
           unresolved=lambda d: int(d["ai_process_ids"].str.contains("UNMAPPED").sum())),
    Plugin("ingredient", ["ledgers/ingredients/alias_a1_v0.csv"], _csv, key="alias", freq="ingredient_id",
           roles={"outcome": "outcome", "provenance": "rule_id"},
           unresolved=lambda d: int((d["outcome"] == "UNRESOLVED").sum())),
    Plugin("molecule", ["ledgers/molecules/mol_v0.jsonl"], _jsonl, key="mol_id",
           validate=lambda d: [m for m, ok in zip(d["mol_id"], d["inchikey_roundtrip_ok"], strict=True) if not ok]),
    Plugin("process", ["ledgers/process/proc_v0.csv"], _csv, key="proc_id", freq="family_id",
           roles={"axis": "axis", "status": "status", "source": "source"}),
    Plugin("quantity", ["ledgers/units/unit_map_v0.csv"], _csv, freq="type", roles={"status": "value_status", "locale": "locale"},
           unresolved=lambda d: int((d["value_status"] == "UNKNOWN").sum())),
    Plugin("ner", ["registry/ner_resources.csv"], _csv, key="resource_id",
           roles={"licence_verified": "licence_verified", "kind": "kind", "availability": "availability"}),
    Plugin("state_graph", ["gold"], _gold_load, key="file",
           validate=lambda d: [f for f, v, inv in zip(d["file"], d["valid"], d["expected_invalid"], strict=True) if v == inv]),
    Plugin("benchmark", ["benchmark/authoring"], _benchmark_load, key="item_id", freq="task_type",
           roles={"origin": "origin", "split": "split"}),
    Plugin("transition", ["experiments/DEL2/runs"], _transition_load, key="run"),
]}


def profile(p: Plugin) -> dict:
    present = [x for x in p.paths if (ROOT / x).exists()]
    if not present:
        return {"plugin": p.name, "available": False, "reason": f"inputs missing: {p.paths}"}
    df = p.load(present)
    if df is None or len(df) == 0:
        return {"plugin": p.name, "available": True, "rows": 0, "note": "no rows yet"}
    h = hashlib.sha256()
    for x in present:
        f = ROOT / x
        for g in ([f] if f.is_file() else sorted(f.rglob("*"))):
            if g.is_file():
                h.update(g.read_bytes())
    flat = df.astype(str)
    out = {"plugin": p.name, "available": True, "inputs": present, "sha256": h.hexdigest(), "rows": int(len(df)),
           "columns": int(df.shape[1]), "exact_duplicate_rows": int(flat.duplicated().sum())}
    if p.key and p.key in df:
        out["key_duplicates"] = int(df[p.key].duplicated().sum())
    miss = {}
    for c in df.columns:
        s = flat[c]
        empty = float(((s == "") | (s == "None") | (s == "nan")).mean())
        unk = float(s.isin(UNKNOWN_TOKENS).mean())
        if empty or unk:
            miss[c] = {"empty": round(empty, 4), "unknown": round(unk, 4)}
    out["missingness"] = dict(sorted(miss.items(), key=lambda kv: -(kv[1]["empty"] + kv[1]["unknown"]))[:25])
    if p.freq and p.freq in df:
        vc = df[p.freq].value_counts()
        k = max(1, int(round(len(vc) * 0.1)))
        out["long_tail"] = {"distinct": int(len(vc)), "top10pct_share": round(float(vc.head(k).sum() / vc.sum()), 4),
                            "singletons": int((vc == 1).sum()), "top5": vc.head(5).to_dict()}
    out["distributions"] = {role: df[c].astype(str).value_counts().head(12).to_dict() for role, c in p.roles.items() if c in df}
    if p.conditions:
        out["condition_completeness"] = p.conditions(df)
    if p.validate:
        v = p.validate(df)
        out["validation_failures"] = {"count": len(v), "examples": v[:10]}
    if p.unresolved:
        out["unresolved_mappings"] = p.unresolved(df)
    split = p.roles.get("split")
    if split and split in df and p.key and p.key in df:
        out["split_counts"] = df[split].value_counts().to_dict()
    return out


def render(rep: dict) -> tuple[str, str]:
    lines = [f"# Data report — {rep['plugin']}", ""]
    if not rep.get("available"):
        lines.append(f"Not available: {rep.get('reason')}")
    else:
        for k, v in rep.items():
            if k in ("plugin", "available"):
                continue
            lines.append(f"- **{k}**: `{json.dumps(v, default=str)[:900]}`")
    md = "\n".join(lines) + "\n"
    body = "".join(f"<p>{html.escape(x)}</p>" for x in lines)
    return md, f"<!doctype html><meta charset=utf-8><title>{rep['plugin']} report</title><body style='font-family:system-ui;max-width:1000px;margin:auto;padding:16px'>{body}</body>"


def run(name: str, out: pathlib.Path) -> dict:
    rep = profile(PLUGINS[name])
    out.mkdir(parents=True, exist_ok=True)
    md, page = render(rep)
    (out / "report.md").write_text(md)
    (out / "report.html").write_text(page)
    (out / "summary.json").write_text(json.dumps(rep, indent=1, default=str))
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plugin", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    if a.all:
        reps = {n: run(n, ROOT / "eda" / n / "auto") for n in PLUGINS}
        g = ROOT / "eda/global/auto"
        g.mkdir(parents=True, exist_ok=True)
        (g / "summary.json").write_text(json.dumps(reps, indent=1, default=str))
        idx = ["# Global data report", "", "| Ledger | Rows | Dup keys | Validation failures | Unresolved | sha256 |", "|---|---|---|---|---|---|"]
        for n, r in reps.items():
            idx.append(f"| {n} | {r.get('rows', '—')} | {r.get('key_duplicates', '—')} | "
                       f"{r.get('validation_failures', {}).get('count', '—')} | {r.get('unresolved_mappings', '—')} | "
                       f"`{(r.get('sha256') or '—')[:12]}` |")
        (g / "index.md").write_text("\n".join(idx) + "\n")
        print("\n".join(idx))
        return 0
    rep = run(a.plugin, pathlib.Path(a.out) if a.out else ROOT / "eda" / a.plugin / "auto")
    print(json.dumps({k: rep.get(k) for k in ("rows", "key_duplicates", "validation_failures", "unresolved_mappings")}, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
