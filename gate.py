r"""
K1 — gate harness (delta plan "Verification"; v4.0 AU). Checks every machine-checkable
acceptance line and prints PASS / FAIL / PENDING. Exit 1 only on FAIL. PENDING = waiting on a
human or an external dependency (named in the reason) — never silently passed.

    .venv/bin/python gate.py            # writes logs/gate/gate_<UTC>.json
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
RESULTS: list[dict] = []


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def gate(gid: str, desc: str):
    def deco(fn):
        try:
            status, reason = fn()
        except Exception as e:  # a crashing check is a failing check
            status, reason = "FAIL", f"{type(e).__name__}: {e}"
        RESULTS.append({"gate": gid, "check": desc, "status": status, "reason": reason})
        return fn
    return deco


@gate("G-SNAP", "every pinned raw file exists and matches its SNAP- hash")
def _():
    bad, n = [], 0
    with (ROOT / "ledgers/snapshots/snapshots.csv").open() as fh:
        for r in csv.DictReader(fh):
            n += 1
            p = ROOT / r["local_path"]
            if not p.exists() or sha(p) != r["sha256"]:
                bad.append(r["snap_id"])
    for line in (ROOT / "ledgers/snapshots/authority_snapshots.jsonl").read_text().splitlines():
        r = json.loads(line)
        n += 1
        p = ROOT / r["local_path"] if r.get("local_path") else next((ROOT / "data/raw/authority").glob("*.pdf"))
        if sha(p) != r["sha256"]:
            bad.append(r["snap_id"])
    lit = ROOT / "ledgers/snapshots/literature_snapshots.jsonl"
    if lit.exists():
        for line in lit.read_text().splitlines():
            r = json.loads(line)
            p = ROOT / "data/raw/literature" / f"{r.get('pmcid')}.xml"
            if r.get("kind") == "fulltext" and p.exists():
                n += 1
                if sha(p) != r["sha256"]:
                    bad.append(r["pmcid"])
    return ("FAIL", f"hash mismatch: {bad}") if bad else ("PASS", f"{n} files verified")


@gate("G-LEDGER", "DEL-1 ledger: hash pinned, every row validates, counts match report")
def _():
    from culinarystate.ledger.schema import EvidenceRow
    rep = json.loads((ROOT / "ledgers/evidence/evidence_v0.report.json").read_text())
    p = ROOT / "ledgers/evidence/evidence_v0.jsonl"
    if sha(p) != rep["sha256_jsonl"]:
        return "FAIL", "ledger sha differs from report"
    rows = [EvidenceRow.model_validate_json(x) for x in p.read_text().splitlines()]
    ev = sum(r.evaluable for r in rows)
    if len(rows) != rep["rows"] or ev != rep["evaluable_rows"]:
        return "FAIL", f"rows {len(rows)}/{rep['rows']} evaluable {ev}/{rep['evaluable_rows']}"
    if any(r.tier.value in ("E5", "E6", "E7") and r.evaluable for r in rows):
        return "FAIL", "an E5–E7 row is evaluable"
    return "PASS", f"{len(rows):,} rows, {ev:,} evaluable, sha {rep['sha256_jsonl'][:12]}"


@gate("G-DEL1-SIZE", "DEL-1 contract: ≥1k rows and ≥40 human-verified literature rows")
def _():
    rep = json.loads((ROOT / "ledgers/evidence/evidence_v0.report.json").read_text())
    lit = ROOT / "ledgers/literature/candidates_v0.csv"
    verified = 0
    if lit.exists():
        with lit.open() as fh:
            verified = sum(1 for r in csv.DictReader(fh) if r["is_retention_relevant"] == "yes" and r["verifier"])
    if rep["evaluable_rows"] < 1000:
        return "FAIL", "fewer than 1k evaluable rows"
    if verified < 40:
        return "PENDING", f"{verified}/40 verified literature rows — needs human verification (K8, guideline literature_verification_v0)"
    return "PASS", f"{rep['evaluable_rows']:,} rows; {verified} verified literature rows"


@gate("G-PREREG", "every frozen pre-registration is unchanged; every DEL-2 run used the frozen card")
def _():
    with (ROOT / "registry/preregistration.csv").open() as fh:
        reg = list(csv.DictReader(fh))
    changed = [r["experiment"] for r in reg if sha(ROOT / r["file"]) != r["sha256"]]
    if changed:
        return "FAIL", f"changed after freeze: {changed}"
    card = next(r for r in reg if r["experiment"] == "DEL2-SX-13-01/03/04")["sha256"]
    runs = sorted((ROOT / "experiments/DEL2/runs").glob("*/metrics.json"))
    bad = [m.parent.name for m in runs if json.loads(m.read_text()).get("card_sha256") != card]  # missing = FAIL
    return ("FAIL", f"DEL-2 runs with another card: {bad}") if bad else \
        ("PASS", f"{len(reg)} frozen file(s) unchanged; {len(runs)} DEL-2 run(s) on the frozen card")


@gate("G-UNITS", "no volume/count unit converts to grams (no invented grams)")
def _():
    from culinarystate.quantity.units import Units
    u = Units()
    bad = []
    with (ROOT / "ledgers/units/unit_map_v0.csv").open() as fh:
        for r in csv.DictReader(fh):
            if r["dimension"] != "mass" and u.to_grams(r["unit_id"], 1.0).status != "UNKNOWN":
                bad.append(r["unit_id"])
    return ("FAIL", f"{bad}") if bad else ("PASS", "all non-mass units → UNKNOWN grams")


@gate("G-REPLAY", "state replay is deterministic on every gold fixture")
def _():
    from culinarystate.state_graph.engine import replay
    from culinarystate.state_graph.gold import load_gold
    files = sorted((ROOT / "gold/fixtures").glob("*.yaml"))
    bad = [f.name for f in files if replay(load_gold(f).events).digest() != load_gold(f).graph.digest()]
    return ("FAIL", f"{bad}") if bad else ("PASS", f"{len(files)} gold files")


@gate("G-ALLERGEN", "allergen classes come only from the FSSAI snapshot; inferred terms flagged")
def _():
    snap = json.loads((ROOT / "ledgers/snapshots/authority_snapshots.jsonl").read_text().splitlines()[0])["sha256"]
    with (ROOT / "ledgers/authority/allergen_v0.csv").open() as fh:
        cls = list(csv.DictReader(fh))
    if any(r["snapshot_sha256"] != snap for r in cls):
        return "FAIL", "allergen class not tied to the FSSAI snapshot"
    with (ROOT / "ledgers/authority/allergen_lexicon_v0.csv").open() as fh:
        inferred = sum(1 for r in csv.DictReader(fh) if r["provenance"] != "EXPLICIT_SOURCE")
    return ("PENDING", f"{len(cls)} classes OK; {inferred} INFERRED_LLM lexicon terms await human review") if inferred \
        else ("PASS", f"{len(cls)} classes")


@gate("G-MOL", "every MOL- record resolves and its InChIKey round-trips")
def _():
    r = json.loads((ROOT / "ledgers/molecules/mol_v0.report.json").read_text())
    ok = r["resolved"] == r["names"] == r["inchikey_roundtrip_ok"]
    return ("PASS" if ok else "FAIL"), f"{r['inchikey_roundtrip_ok']}/{r['names']}"


@gate("G-DEMO", "every demo scenario runs and every cited EVD- id exists")
def _():
    from culinarystate.demo.scenarios import cited_ok, run_all
    rs = run_all()
    bad = [r["id"] for r in rs if not cited_ok(r)]
    return ("FAIL", f"{bad}") if bad else ("PASS", f"{len(rs)} scenarios")


@gate("G-BENCH", "benchmark test split hash frozen before any locked run (AH13)")
def _():
    f = ROOT / "benchmark/FROZEN.sha256"
    return ("PASS", f.read_text().strip()[:16]) if f.exists() else \
        ("PENDING", "no human-authored benchmark yet (J2) — locked runs (K14, H3) not allowed")


@gate("G-RECIPEDB", "DEL-3 input available (RecipeDB + RecipeDB3 annotations)")
def _():
    d = ROOT / "data/raw/recipedb"
    return ("PASS", "present") if d.exists() and any(d.iterdir()) else \
        ("PENDING", "RecipeDB access not yet granted (WP-03 email, H1) — blocks DEL-3 pilot, Gold, sessions")


def main() -> int:
    out = ROOT / "logs/gate"
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (out / f"gate_{ts}.json").write_text(json.dumps(RESULTS, indent=2))
    w = max(len(r["gate"]) for r in RESULTS)
    for r in RESULTS:
        print(f"{r['status']:8} {r['gate']:<{w}}  {r['check']}\n{'':8} {'':<{w}}  → {r['reason']}")
    fails = sum(r["status"] == "FAIL" for r in RESULTS)
    print(f"\n{sum(r['status'] == 'PASS' for r in RESULTS)} PASS · {sum(r['status'] == 'PENDING' for r in RESULTS)} PENDING · {fails} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
