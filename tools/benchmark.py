r"""
J2 — DEL-5 benchmark tooling: validate | stats | freeze  (delta plan §6; v4.0 AH5, AH13).

    .venv/bin/python tools/benchmark.py validate        # every authoring file, all rules below
    .venv/bin/python tools/benchmark.py stats           # counts per task type → achieved tier
    .venv/bin/python tools/benchmark.py freeze          # deterministic split + hashes (curator only)

Items are written by HUMANS in benchmark/authoring/*.yaml (see benchmark/README.md). The tool
never writes or edits an item. Freeze assigns dev/test per task type deterministically
(sha256 of item_id), writes benchmark/{dev,test}.jsonl and benchmark/FROZEN.sha256, and
appends to registry/preregistration.csv. After freeze nothing is tuned on test labels (AH13).
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import sys
from collections import Counter
from datetime import datetime, timezone

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
B = ROOT / "benchmark"
TASKS = ("state", "next_action", "constraints", "diagnosis", "recovery", "process_effect", "conflict", "abstain")
MODES = ("ANSWER", "COMPARE", "ASK", "DIAGNOSE", "RECOVER", "RECOMMEND", "ABSTAIN")
REGIMES = ("observed", "near", "qualitative", "conflict", "unsupported", "not_applicable")
SESSION_TASKS = ("state", "next_action", "constraints", "diagnosis", "recovery")
TIERS = (("stretch", 440), ("target", 320), ("minimum", 104))
DEV_SHARE = 0.25                                       # 80 dev / 240 test at the target tier
REQUIRED = ("item_id", "task_type", "question", "gold_mode", "gold_answer", "evidence_regime", "must_abstain",
            "difficulty", "author", "reviewer")


def load_items() -> list[dict]:
    items = []
    for f in sorted((B / "authoring").glob("*.yaml")):
        for k, it in enumerate(yaml.safe_load(f.read_text()) or []):
            it["_file"] = f"{f.name}#{k}"
            items.append(it)
    return items


def validate(items: list[dict]) -> list[str]:
    from culinarystate.ner.scorer import leakage_audit
    errs = []
    ev_ids = {json.loads(x)["evidence_id"] for x in (ROOT / "ledgers/evidence/evidence_v0.jsonl").read_text().splitlines()}
    seen = Counter(it.get("item_id") for it in items)
    for it in items:
        w = f"{it['_file']} ({it.get('item_id')})"
        for k in REQUIRED:
            if it.get(k) in (None, ""):
                errs.append(f"{w}: missing {k}")
        if seen[it.get("item_id")] > 1:
            errs.append(f"{w}: duplicate item_id")
        if it.get("task_type") not in TASKS:
            errs.append(f"{w}: task_type must be one of {TASKS}")
        if it.get("gold_mode") not in MODES:
            errs.append(f"{w}: gold_mode must be one of {MODES}")
        if it.get("evidence_regime") not in REGIMES:
            errs.append(f"{w}: evidence_regime must be one of {REGIMES}")
        if it.get("author") and it.get("author") == it.get("reviewer"):
            errs.append(f"{w}: reviewer must differ from author")
        req = it.get("required_evidence_ids") or []
        if bad := [e for e in req if e not in ev_ids]:
            errs.append(f"{w}: unknown evidence ids {bad}")
        if it.get("must_abstain"):
            if it.get("gold_mode") != "ABSTAIN" or req:
                errs.append(f"{w}: must_abstain items need gold_mode ABSTAIN and no required evidence")
        if it.get("task_type") == "process_effect" and it.get("evidence_regime") in ("observed", "near") and not req:
            errs.append(f"{w}: observed/near process_effect items need required_evidence_ids")
        if it.get("task_type") in SESSION_TASKS:
            s = it.get("session") or {}
            if not s.get("recipe_id"):
                errs.append(f"{w}: session tasks need session.recipe_id")
            elif str(s["recipe_id"]).startswith("FIX-"):
                errs.append(f"{w}: FIX- recipes appear in tests/demo — contamination; use RecipeDB recipes")
    # contamination: no near-copy of the demo scenarios or DEL-4 dev queries
    from culinarystate.demo.scenarios import SCENARIOS
    known = {f"demo:{sid}": q for sid, _, q, _ in SCENARIOS}
    dev = ROOT / "experiments/DEL4/dev/queries.jsonl"
    if dev.exists():
        known |= {f"del4dev:{k}": json.loads(x)["text"] for k, x in enumerate(dev.read_text().splitlines())}
    leak = leakage_audit(known, {it["item_id"]: it.get("question", "") for it in items if it.get("item_id")}, jaccard=0.6, n=3)
    for k, src in leak["exact_duplicates"]:
        errs.append(f"{k}: question duplicates {src}")
    for k, src, j in leak["near_duplicates"]:
        errs.append(f"{k}: question near-duplicates {src} (Jaccard {j})")
    return errs


def tier(n: int) -> str:
    return next((name for name, t in TIERS if n >= t), "below_minimum")


def stats(items):
    c = Counter(it.get("task_type") for it in items)
    return {"items": len(items), "by_task": dict(sorted(c.items())), "achieved_tier": tier(len(items)),
            "min_per_task": min((c.get(t, 0) for t in TASKS), default=0)}


def freeze(items):
    if errs := validate(items):
        raise SystemExit("refusing to freeze: validation errors\n" + "\n".join(errs[:30]))
    if (B / "FROZEN.sha256").exists():
        raise SystemExit("already frozen — a re-freeze needs a DECISIONS.md entry and deleting FROZEN.sha256 by a human")
    dev, test = [], []
    for t in TASKS:
        group = sorted((it for it in items if it["task_type"] == t),
                       key=lambda it: hashlib.sha256(it["item_id"].encode()).hexdigest())
        k = round(len(group) * DEV_SHARE)
        dev += group[:k]
        test += group[k:]
    clean = lambda xs: "\n".join(json.dumps({k: v for k, v in x.items() if k != "_file"}, sort_keys=True, ensure_ascii=False)
                                 for x in xs) + "\n"  # noqa: E731
    (B / "dev.jsonl").write_text(clean(dev))
    (B / "test.jsonl").write_text(clean(test))
    h = {f: hashlib.sha256((B / f).read_bytes()).hexdigest() for f in ("dev.jsonl", "test.jsonl")}
    (B / "FROZEN.sha256").write_text(f"{h['test.jsonl']}  test.jsonl\n{h['dev.jsonl']}  dev.jsonl\n")
    with (ROOT / "registry/preregistration.csv").open("a", newline="") as fh:
        csv.writer(fh).writerow(["DEL5-benchmark", "benchmark/test.jsonl", h["test.jsonl"],
                                 datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                 f"curator role (AH13); tier {tier(len(items))}; dev {len(dev)} test {len(test)}"])
    return {"dev": len(dev), "test": len(test), **h}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "validate"
    items = load_items()
    if cmd == "validate":
        e = validate(items)
        print("\n".join(e) if e else f"OK — {len(items)} items valid")
        sys.exit(1 if e else 0)
    print(json.dumps(stats(items) if cmd == "stats" else freeze(items), indent=1))
