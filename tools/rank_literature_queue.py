r"""
K8 — ranked verification queue from ALL AI pre-check output (v0 cells, v1-new cells, round-2 cells).
    .venv/bin/python tools/rank_literature_queue.py
Outputs: ledgers/literature/verification_queue_ranked_v1.csv and eda/literature/literature_cell_precheck_report.html

Deterministic checks per pre-checked cell (no LLM): schema, source existence (XML present; sha matches its SNAP),
DOI/source dedup, matrix (food) present, process mapped (no PROC-UNMAPPED), target present, unit present, basis
stated, condition completeness (T, t stated), primary vs secondary (aggregate flag), independent-source lineage
(distinct papers per ingredient×process×target), possible contradiction (opposite raw→processed directions across
papers, from parsed values of the cell and its raw counterpart), exact span (verbatim quote present).

Categories:
  REJECT           not relevant / extraction error / statistic column
  COUNTERPART      raw/untreated reference cells (kept as support for processed cells; not queued alone)
  P4_CONFLICT      relevant and in a cross-paper direction conflict group → human adjudication
  P3_NEEDS_SOURCE  relevant but secondary/aggregate, processed value without raw counterpart, ambiguous header,
                   counterpart missing from extraction, or low confidence
  P1_VERIFY_NOW    high confidence; RETENTION_REPORTED or PROCESSED_VALUE with counterpart; process mapped; target,
                   unit and verbatim quote present
  P2_GOOD_CANDIDATE every other relevant cell
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import pathlib
import re
from collections import defaultdict

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
LIT = ROOT / "ledgers/literature"
ENUM_ROLE = {"RETENTION_REPORTED", "PROCESSED_VALUE", "RAW_REFERENCE", "STAT_OR_SD", "OTHER", "EXTRACT_ERROR"}


def load_cells():
    v0 = pd.read_csv(LIT / "candidates_v0.csv", keep_default_na=False)
    v1 = pd.read_csv(LIT / "candidates_v1.csv", keep_default_na=False)
    r2 = pd.read_csv(LIT / "candidates_r2.csv", keep_default_na=False) if (LIT / "candidates_r2.csv").exists() else None
    v0to1 = dict(zip(v1.v0_cand_id, v1.cand_id))
    cells = {r.cand_id: r._asdict() for r in v1.itertuples(index=False)}
    if r2 is not None:
        cells.update({r.cand_id: r._asdict() for r in r2.itertuples(index=False)})
    return v0to1, cells


def load_precheck(v0to1):
    recs, tables = {}, {}
    for d, use_map in (("ai_precheck", True), ("ai_precheck_v1new", False), ("ai_precheck_r2", False)):
        for f in sorted((LIT / d).glob("PMC*.jsonl")) if (LIT / d).exists() else []:
            for line in f.read_text().splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                if r.get("type") == "table":
                    tables[(r["pmcid"], r["table"])] = r
                elif r.get("type") == "cell":
                    cid = v0to1.get(r["cand_id"], "") if use_map else r["cand_id"]
                    if cid:
                        if use_map and r.get("ai_raw_counterpart_cand_id"):
                            r["ai_raw_counterpart_cand_id"] = v0to1.get(r["ai_raw_counterpart_cand_id"], "")
                        recs[cid] = r
    return recs, tables


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main() -> int:
    v0to1, cells = load_cells()
    recs, tables = load_precheck(v0to1)
    snaps = {}
    for line in (ROOT / "ledgers/snapshots/literature_snapshots.jsonl").read_text().splitlines():
        s = json.loads(line)
        if s.get("kind") == "fulltext" and s.get("status", 200) == 200:
            snaps[s["pmcid"]] = s
    sha_ok = {}
    for p in {r["pmcid"] for r in recs.values()}:
        f = ROOT / f"data/raw/literature/{p}.xml"
        sha_ok[p] = f.exists() and p in snaps and hashlib.sha256(f.read_bytes()).hexdigest() == snaps[p]["sha256"]
    doi_papers = defaultdict(set)
    for p, s in snaps.items():
        if s.get("doi"):
            doi_papers[s["doi"].lower()].add(p)
    rows = []
    for cid, r in recs.items():
        c = cells.get(cid, {})
        t = tables.get((r["pmcid"], r.get("table")), {})
        flags = r.get("ai_flags") or []
        flags = flags if isinstance(flags, list) else [flags]
        procs = [x.strip() for x in (r.get("ai_process_ids") or "").split(";") if x.strip()]
        cond = r.get("ai_conditions") or ""
        row = {"cand_id": cid, "pmcid": r["pmcid"], "family": c.get("family", ""), "table": r.get("table"),
               "row_header": c.get("row_header", ""), "col_header": c.get("col_header", ""),
               "cell_verbatim": c.get("cell_verbatim", ""), "parsed_value": c.get("parsed_value", ""),
               "raw_counterpart_cand_id": r.get("ai_raw_counterpart_cand_id", ""),
               "raw_counterpart_verbatim": cells.get(r.get("ai_raw_counterpart_cand_id", ""), {}).get("cell_verbatim", ""),
               **{k: r.get(k, "") for k in ("ai_relevant", "ai_role", "ai_food", "ai_ingredient_id", "ai_process_text",
                                            "ai_process_ids", "ai_conditions", "ai_target", "ai_value_kind", "ai_unit",
                                            "ai_confidence", "ai_quote")},
               "ai_flags": ";".join(flags), "table_basis": t.get("basis", ""),
               "table_retention_method": t.get("retention_method", ""), "paper_url": f"https://europepmc.org/article/PMC/{r['pmcid']}"}
        chk = {"schema_ok": r.get("ai_role") in ENUM_ROLE and r.get("ai_relevant") in ("yes", "no") and bool(c),
               "source_ok": sha_ok.get(r["pmcid"], False),
               "dup_source": len(doi_papers.get((snaps.get(r["pmcid"], {}).get("doi") or "").lower(), ())) > 1,
               "matrix_ok": bool(r.get("ai_food")), "process_mapped": bool(procs) and not any("UNMAPPED" in p for p in procs),
               "target_ok": bool(r.get("ai_target")), "unit_ok": bool(r.get("ai_unit")),
               "basis_stated": t.get("basis") in ("WET", "DRY"),
               "cond_T": bool(re.search(r"\bT\s*=", cond)), "cond_t": bool(re.search(r"\bt\s*=", cond)),
               "secondary": "review_aggregate_cited_study" in flags, "span_ok": bool(r.get("ai_quote"))}
        row.update(chk)
        row["condition_completeness"] = int(chk["cond_T"]) + int(chk["cond_t"])
        rows.append(row)
    df = pd.DataFrame(rows)
    rel = df["ai_relevant"] == "yes"
    # lineage + contradiction on relevant processed cells with counterparts
    key = df["ai_ingredient_id"].str.lower() + "|" + df["ai_process_ids"] + "|" + df["ai_target"].str.lower().str.strip()
    df["lineage_key"] = key
    df["independent_papers"] = df["lineage_key"].map(df[rel].groupby("lineage_key")["pmcid"].nunique()).fillna(0).astype(int)
    def direction(r):
        a, b = num(r["parsed_value"]), num(cells.get(r["raw_counterpart_cand_id"], {}).get("parsed_value"))
        if a is None or b is None or b == 0:
            return ""
        return "up" if a > b else "down" if a < b else "same"
    df["direction"] = [direction(r) if (r["ai_role"] == "PROCESSED_VALUE" and r["raw_counterpart_cand_id"]) else ""
                       for _, r in df.iterrows()]
    dirs = df[rel & (df["direction"] != "")].groupby("lineage_key").agg(
        ups=("direction", lambda s: (s == "up").sum()), downs=("direction", lambda s: (s == "down").sum()),
        papers=("pmcid", "nunique"))
    conflict_keys = set(dirs[(dirs.ups > 0) & (dirs.downs > 0) & (dirs.papers > 1)].index)

    def category(r):
        if r["ai_relevant"] != "yes" or r["ai_role"] in ("EXTRACT_ERROR", "STAT_OR_SD") or not r["schema_ok"]:
            return "REJECT"
        if r["ai_role"] == "RAW_REFERENCE":
            return "COUNTERPART"
        if r["lineage_key"] in conflict_keys:
            return "P4_CONFLICT"
        fl = r["ai_flags"]
        if (r["secondary"] or (r["ai_role"] == "PROCESSED_VALUE" and not r["raw_counterpart_cand_id"])
                or "ambiguous_header" in fl or "counterpart_not_in_candidates" in fl or r["ai_confidence"] == "low"
                or not r["source_ok"]):
            return "P3_NEEDS_SOURCE"
        if (r["ai_confidence"] == "high" and r["ai_role"] in ("RETENTION_REPORTED", "PROCESSED_VALUE") and r["process_mapped"]
                and r["target_ok"] and r["unit_ok"] and r["span_ok"]):
            return "P1_VERIFY_NOW"
        return "P2_GOOD_CANDIDATE"
    df["queue_category"] = df.apply(category, axis=1)
    order = {"P1_VERIFY_NOW": 0, "P4_CONFLICT": 1, "P2_GOOD_CANDIDATE": 2, "P3_NEEDS_SOURCE": 3, "COUNTERPART": 4, "REJECT": 5}
    df["_o"] = df["queue_category"].map(order)
    df = df.sort_values(["_o", "condition_completeness", "independent_papers", "family", "pmcid", "cand_id"],
                        ascending=[True, False, False, True, True, True]).drop(columns="_o")
    df.insert(0, "queue_rank", range(1, len(df) + 1))
    for h in ("is_retention_relevant", "verifier", "verified_utc", "human_notes"):
        df[h] = ""
    df.to_csv(LIT / "verification_queue_ranked_v1.csv", index=False)
    # ---- HTML report
    out = ROOT / "eda/literature"
    out.mkdir(parents=True, exist_ok=True)
    cat = df["queue_category"].value_counts().reindex(order).fillna(0).astype(int)
    fam = pd.crosstab(df["family"], df["queue_category"]).reindex(columns=list(order), fill_value=0)
    checks = df[rel][["source_ok", "matrix_ok", "process_mapped", "target_ok", "unit_ok", "basis_stated", "cond_T", "cond_t",
                      "secondary", "span_ok", "dup_source"]].mean().round(3)
    p1 = df[df.queue_category == "P1_VERIFY_NOW"].head(60)[["queue_rank", "family", "ai_food", "ai_process_text", "ai_target",
                                                           "cell_verbatim", "raw_counterpart_verbatim", "ai_unit", "pmcid"]]
    conf = df[df.queue_category == "P4_CONFLICT"][["lineage_key", "pmcid", "direction", "cell_verbatim", "raw_counterpart_verbatim"]]
    css = ("body{font-family:system-ui,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:#1d2420;background:#f7f8f6}"
           "table{border-collapse:collapse;font-size:12.5px;margin:8px 0 20px}th,td{border:1px solid #d6ddd8;padding:4px 7px;text-align:left}"
           "th{background:#e8eee9}h1{font-size:22px}h2{font-size:17px;margin-top:28px}.note{color:#55625a;font-size:13px}")
    parts = [f"<!doctype html><meta charset=utf-8><title>Literature cell pre-check</title><style>{css}</style>",
             "<h1>Literature cell pre-check — ranked verification queue v1</h1>",
             f"<p class=note>{len(df):,} pre-checked cells from {df.pmcid.nunique()} open-access papers. AI pre-check (labels only) + deterministic checks. "
             "Nothing here is verified evidence until a human fills <code>verifier</code>. Source: <code>ledgers/literature/verification_queue_ranked_v1.csv</code>.</p>",
             "<h2>Queue categories</h2>", cat.rename("cells").to_frame().to_html(),
             "<h2>By anchor family</h2>", fam.to_html(),
             "<h2>Deterministic checks (share of relevant cells passing)</h2>", checks.rename("share").to_frame().to_html(),
             f"<h2>Possible cross-paper contradictions ({len(conflict_keys)} groups)</h2>",
             "<p class=note>Opposite raw→processed direction for the same ingredient × process × target in different papers. A human must adjudicate; conditions often differ.</p>",
             conf.to_html(index=False, escape=True) if len(conf) else "<p>none</p>",
             "<h2>First 60 P1_VERIFY_NOW cells</h2>", p1.to_html(index=False, escape=True)]
    (out / "literature_cell_precheck_report.html").write_text("\n".join(parts))
    print(cat.to_dict())
    print("relevant cells:", int(rel.sum()), "| papers:", df.pmcid.nunique(), "| conflict groups:", len(conflict_keys))
    print("check pass rates:", checks.to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
