r"""T04: only human-signed rows are promoted; values come from the verbatim cell; derived retention is logged;
unmapped processes are rejected, not guessed. Uses a temp copy of the queue with a SIMULATED signature (test only)."""
import csv
import json
import pathlib

from tools.promote_literature import conditions, main

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_promotion_rules(tmp_path):
    q = list(csv.DictReader((ROOT / "ledgers/literature/verification_queue_ranked_v1.csv").open(encoding="utf-8")))
    proc = next(r for r in q if r["queue_category"] == "VERIFY_NOW" and r["ai_role"] == "PROCESSED_VALUE"
                and r["raw_counterpart_cand_id"] and r["ai_value_kind"] == "CONCENTRATION")
    unmapped = next(r for r in q if "UNMAPPED" in r["ai_process_ids"])
    raw = next(r for r in q if r["cand_id"] == proc["raw_counterpart_cand_id"])          # support row, unsigned
    unsigned = next(r for r in q if r["cand_id"] not in (proc["cand_id"], unmapped["cand_id"], raw["cand_id"]))
    for r in (proc, unmapped):
        r.update(is_retention_relevant="yes", verifier="TEST-ONLY", verified_utc="2026-10-13T00:00:00Z")
    path = tmp_path / "queue.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(q[0]))
        w.writeheader()
        w.writerows([proc, unmapped, raw, unsigned])
    main(["--queue", str(path), "--out", str(tmp_path), "--id-map", str(tmp_path / "ids.csv")])
    rows = [json.loads(x) for x in (tmp_path / "literature_v1.jsonl").read_text().splitlines()]
    assert {r["verification"]["verifier"] for r in rows} == {"TEST-ONLY"}
    assert any(r["provenance"] == "DERIVED_DETERMINISTIC" and r["value_kind"] == "RETENTION_PERCENT" for r in rows)
    assert all(r["evidence_id"] >= "EVD-100001" for r in rows)
    rej = list(csv.DictReader((tmp_path / "literature_v1.rejects.csv").open()))
    assert [x["cand_id"] for x in rej] == [unmapped["cand_id"]] and "not mapped" in rej[0]["reason"]
    first = (tmp_path / "ids.csv").read_text()
    main(["--queue", str(path), "--out", str(tmp_path), "--id-map", str(tmp_path / "ids.csv")])
    assert (tmp_path / "ids.csv").read_text() == first                    # re-run never renumbers


def test_condition_parsing_never_invents():
    c = conditions("T=100C(MEASURED); t=15 min(MEASURED); medium=water(QUALITATIVE); t2=bad")
    assert c["T"] == {"status": "MEASURED", "value": 100.0, "unit": "degC", "raw": "100C"}
    assert c["t"]["value"] == 15.0 and c["medium"]["status"] == "QUALITATIVE" and "t2" not in c
