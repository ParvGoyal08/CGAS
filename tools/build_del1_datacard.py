r"""
K9 — DEL-1 data card + EDA (SSOT §203.9; master prompt Part M §§1–5, 10, 13; v4.0 AA1).

    .venv/bin/python tools/build_del1_datacard.py

Writes eda/evidence/v0/report.md, report.html and figures. Hypotheses that the EDA
suggests are logged to registry/hypotheses.csv at ladder level L1 only — nothing is
promoted from EDA (Part N).
"""
from __future__ import annotations

import html
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "eda/evidence/v0"
LEDGER = ROOT / "ledgers/evidence/evidence_v0.parquet"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(LEDGER)
    rep = json.loads((ROOT / "ledgers/evidence/evidence_v0.report.json").read_text())
    ev = df[df["defect"].isna()].copy()
    ev["nclass"] = ev["notes"].str.extract(r"nutrient_class=([^;]+)")[0]
    ev["code"] = ev["source_record"].str.extract(r"Retn_Code=(\d+)")[0]
    ev["proc_sig"] = ev["process_ids"].where(ev["process_ids"] != "", "") + np.where(
        ev["process_alternatives"] != "", "~" + ev["process_alternatives"], "")
    ev["censored"] = ev["censoring"] == "RIGHT"

    lines = []
    W = lines.append
    W("# DEL-1 data card + EDA — evidence ledger v0\n")
    W(f"Ledger `ledgers/evidence/evidence_v0.jsonl` · sha256 `{rep['sha256_jsonl'][:16]}…` · "
      f"built from `SNAP-0001` (USDA Retention Factors R6, CC0).\n")
    W("## 1. Provenance and licence\n")
    W("| Source | Rows | Licence | Raw storage | Origin type | Tier |\n|---|---|---|---|---|---|")
    W(f"| SRC-0001 USDA Table of Nutrient Retention Factors, Release 6 (2007) | {len(df):,} | CC0 (catalog.data.gov) | allowed | DATABASE_AGGREGATE | E3 |")
    W("\nPhenol-Explorer 3.0 is **not yet ingested** (ADR 0002, awaiting H2). Literature rows: **0 verified**; the ≥40 required are blocked on human verification.\n")
    W("## 2. Size and duplication\n")
    W(f"- rows **{len(df):,}**; evaluable (E1–E4, no defect) **{len(ev):,}**; defects **{df['defect'].notna().sum()}** (retention code 5005: factor missing in source)")
    W(f"- retention codes (food category × preparation) **{ev['code'].nunique()}**; ingredient categories **{ev['ingredient_id'].nunique()}**; "
      f"targets **{ev['target_variable'].nunique()}**; distinct process signatures **{ev['proc_sig'].nunique()}**")
    vec = ev.pivot_table(index="code", columns="target_code", values="value", aggfunc="first")
    key = vec.fillna(-1).astype(int).astype(str).agg(",".join, axis=1)
    dup = key[key.duplicated(keep=False)]
    W(f"- **duplicate audit:** {dup.index.nunique()} codes share an identical full nutrient vector with another code "
      f"({dup.nunique()} clusters) — consistent with USDA's documented imputation from similar foods/methods; grouped before any split (DEL-2 card §G)\n")
    W("## 3. Schema validity and availability\n")
    W("All rows validate against `EvidenceRow` v1 (Pydantic) on construction.\n")
    W("| Field | Available (non-UNKNOWN) |\n|---|---|")
    for col, name in (("cond_t_status", "time"), ("cond_T_status", "temperature"), ("cond_water_handling_status", "water handling"),
                      ("cond_medium_status", "medium"), ("state_in", "state_in"), ("food_form", "food form")):
        if col in ev:
            avail = ev[col].notna() & (ev[col] != "UNKNOWN")
            W(f"| {name} | {avail.mean():.1%} ({int(avail.sum()):,} rows) |")
        else:
            W(f"| {name} | 0.0% (absent) |")
    W("\nTemperature is UNKNOWN for **every** row: R6 states preparation methods, not temperatures. Times are stated for some legume, milk and alcohol preparations only.\n")
    W("## 4. Distributions\n")
    W("Retention values are integer percent reported **to the nearest 5%**, with values above 100 reported as 100 (right-censored).\n")
    W("| Nutrient class | Rows | Median % | IQR | Share censored at 100 |\n|---|---|---|---|---|")
    for c, g in ev.groupby("nclass"):
        q1, q3 = g["value"].quantile([.25, .75])
        W(f"| {c} | {len(g):,} | {g['value'].median():.0f} | {q1:.0f}–{q3:.0f} | {g['censored'].mean():.0%} |")
    fig, ax = plt.subplots(figsize=(8, 4))
    order = ev.groupby("nclass")["value"].median().sort_values().index
    ax.boxplot([ev.loc[ev["nclass"] == c, "value"] for c in order], tick_labels=list(order), orientation="horizontal")
    ax.set_xlabel("retention (% of raw, reported to nearest 5; capped at 100)")
    ax.set_title("USDA R6 retention by nutrient class")
    fig.tight_layout()
    fig.savefig(OUT / "retention_by_class.png", dpi=130)
    plt.close(fig)
    W("\n![retention by nutrient class](retention_by_class.png)\n")
    pf = ev.drop_duplicates("code")["proc_sig"].value_counts()
    W(f"**Process long tail:** {len(pf)} process signatures over {ev['code'].nunique()} codes; the top 5 cover "
      f"{pf.head(5).sum() / pf.sum():.0%} of codes; {int((pf == 1).sum())} signatures occur once.\n")
    W("## 5. Coverage and sparsity\n")
    pair = ev.drop_duplicates("code").groupby(["ingredient_id", "proc_sig"]).size().unstack(fill_value=0)
    W(f"Ingredient × process-signature matrix: **{pair.shape[0]} × {pair.shape[1]}**, filled cells **{(pair > 0).sum().sum()}** "
      f"of {pair.size} (**{(pair > 0).sum().sum() / pair.size:.1%}** density). At the code × nutrient level the table is "
      f"nearly dense ({len(ev):,} of {ev['code'].nunique() * ev['target_code'].nunique():,} cells). **Sparsity lives in which food×process pairs were ever studied, "
      f"not in which nutrients were measured** — the case SX-13-04 models.\n")
    top_proc = pf.head(25).index
    sub = pair.loc[:, [c for c in top_proc if c in pair.columns]]
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.imshow((sub > 0).to_numpy(), aspect="auto", cmap="Greys")
    ax.set_yticks(range(len(sub.index)), [s.replace("ING-", "") for s in sub.index], fontsize=7)
    ax.set_xticks(range(len(sub.columns)), [c.replace("PROC-", "")[:28] for c in sub.columns], rotation=90, fontsize=7)
    ax.set_title("Which food × process pairs USDA R6 covers (25 most common process signatures)")
    fig.tight_layout()
    fig.savefig(OUT / "coverage_food_x_process.png", dpi=130)
    plt.close(fig)
    W("![coverage](coverage_food_x_process.png)\n")
    cw = ROOT / "ledgers/ingredients/crosswalk_a1_v0.report.json"
    if cw.exists():
        c = json.loads(cw.read_text())
        s = c["mention_share_by_outcome"]
        W("### 5b. Coverage of a real recipe vocabulary (K6/P12)\n")
        W(f"Against the A1 course corpus ({c['mentions']:,} ingredient mentions, {c['distinct_names']:,} names; "
          "rule crosswalk `ledgers/ingredients/alias_a1_v0.csv`, all links PROPOSED):\n")
        W("| Outcome | Share of mentions |\n|---|---|")
        for k, v in s.items():
            W(f"| {k} | {v:.1%} |")
        W(f"\nOnly **{s.get('MAPPED_CONCEPT', 0) + s.get('MAPPED_CATEGORY', 0):.1%}** of recipe ingredient mentions reach any R6 "
          f"food, and only **{s.get('MAPPED_CONCEPT', 0):.1%}** at concept level; the rest are category links (e.g. garlic → "
          "`VEG,OTHER`), derived products (stock, juice, purée), or classes R6 never measures (herbs, spices, fats, sugars). "
          "This bounds what DEL-4/5 can answer from R6 alone.\n")
    W("## 10. Bias audit\n")
    fg = ev.drop_duplicates("code")["food_group"].value_counts()
    W("- food groups by number of preparation codes: " + ", ".join(f"{k.replace('USDA-FdGrp-', 'group ')} {v}" for k, v in fg.items()))
    W("- **US-centric** (USDA, 1975–2007 compilations); **no Indian preparations** (tadka, dum, pressure cooking) are covered — relevant to the Indian-recipe use case")
    W("- category-level foods (e.g. `VEG,ROOTS,ETC`) dominate several groups → linking to specific RecipeDB ingredients is one-to-many")
    W("- source-level imputation (USDA-documented) cannot be separated per row\n")
    W("## 13. Hypotheses generated (logged at ladder L1 — **not** claims)\n")
    hyps = [
        ("HYP-0001", "Water-soluble vitamins show lower retention than minerals across preparations in R6", "EDA §4 medians"),
        ("HYP-0002", "Processes that discard cooking water retain less of water-soluble vitamins than those that consume it", "water-handling field"),
        ("HYP-0003", "Study coverage (which food×process pairs exist) is non-random by food group", "EDA §5 density"),
    ]
    W("| ID | Pattern | Basis |\n|---|---|---|")
    for h in hyps:
        W(f"| {h[0]} | {h[1]} | {h[2]} |")
    (ROOT / "registry").mkdir(exist_ok=True)
    hp = ROOT / "registry/hypotheses.csv"
    if not hp.exists():
        hp.write_text("hyp_id,statement,ladder_level,source,status\n")
    existing = hp.read_text()
    with hp.open("a") as fh:
        for h in hyps:
            if h[0] not in existing:
                fh.write(f'{h[0]},"{h[1]}",L1,"EDA evidence v0: {h[2]}",OPEN\n')
    md = "\n".join(lines) + "\n"
    (OUT / "report.md").write_text(md)
    body = "".join(f"<p>{html.escape(l)}</p>\n" if not l.startswith("![") else
                   f'<img src="{l.split("(")[1].rstrip(")")}" style="max-width:100%">\n' for l in lines)
    (OUT / "report.html").write_text(f"<!doctype html><meta charset=utf-8><title>DEL-1 data card v0</title><body style='font-family:sans-serif;max-width:900px;margin:auto'>{body}</body>")
    print(md[:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
