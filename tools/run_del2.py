r"""
Run DEL-2 exactly as pre-registered (experiments/DEL2/card.md).

    .venv/bin/python tools/run_del2.py [--quick]

Refuses to run if the card's SHA-256 differs from registry/preregistration.csv.
Writes experiments/DEL2/runs/<run-id>/{metrics.json, oof.parquet} and prints a summary.
--quick: seed 1 only and no inner CV (for smoke testing; not a reportable run).
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from culinarystate.transition import del2 as D  # noqa: E402

CARD = ROOT / "experiments/DEL2/card.md"


def check_prereg():
    want = next(r["sha256"] for r in csv.DictReader((ROOT / "registry/preregistration.csv").open())
                if r["file"] == "experiments/DEL2/card.md")
    got = hashlib.sha256(CARD.read_bytes()).hexdigest()
    if want != got:
        sys.exit(f"pre-registration mismatch: card changed after freeze ({got[:12]} ≠ {want[:12]})")
    return got


def run(cells, cluster, split, seed, quick):
    folds = D.make_folds(cells, split, seed, cluster)
    models = {"D0": [], "D1": [], "D2": [], "D3": [], "D4": [], "D5": [], "D5-noproc": [],
              "D7": [], "D7-noproc": [], "MF-biased": []}
    oof = {m: np.full(len(cells), np.nan) for m in models}
    conformal = {"D5": [], "D7": []}
    chosen = []
    for k in range(D.N_FOLDS):
        trm, tem = folds != k, folds == k
        tr, te = cells[trm], cells[tem]
        oof["D0"][tem] = D.d0(tr, te)
        oof["D1"][tem] = D.d1(tr, te)
        oof["D2"][tem] = D.d2(tr, te)
        oof["D3"][tem] = D.d3(tr, te)
        oof["D4"][tem] = D.d4(tr, te)
        oof["MF-biased"][tem] = D.mf_biased(tr, te, seed=seed)
        for kind, fn in (("d5", D.d5), ("d7", D.d7)):
            for with_proc in (True, False):
                name = kind.upper() + ("" if with_proc else "-noproc")
                params = None if quick else D.inner_select(tr, kind, split, seed, cluster, with_proc)
                chosen.append({"fold": k, "model": name, "params": params})
                oof[name][tem] = fn(tr, te, with_proc=with_proc, params=params, seed=seed)
                if with_proc:   # split-conformal (card J): calibration slice of the training fold
                    cal_mask = (D.make_folds(tr, split, seed + 99, cluster) == 0)
                    fit, cal = tr[~cal_mask], tr[cal_mask]
                    pc = fn(fit, cal, with_proc=True, params=params, seed=seed)
                    res = D.censor_err(cal["y"].to_numpy(), pc, cal["censored"].to_numpy())
                    q = np.quantile(res, min(1.0, 0.9 * (1 + 1 / max(len(res), 1))))
                    yhat = oof[name][tem]
                    y, c = te["y"].to_numpy(), te["censored"].to_numpy()
                    covered = np.where(c, yhat + q >= 97.5, np.abs(y - yhat) <= q)
                    conformal[name.split("-")[0]].append({"fold": k, "q": float(q),
                                                          "coverage": float(covered.mean()),
                                                          "width": float(2 * q)})
    return oof, conformal, chosen, folds


def summarise(cells, oof, split, cluster, seed, prop=None):
    y, c = cells["y"].to_numpy(), cells["censored"].to_numpy()
    g = D.group_ids(cells, split, cluster).to_numpy()
    out = {}
    w = None
    if prop is not None:
        p = np.array([prop["p_of"][(i, s)] for i, s in zip(cells["ingredient"], cells["proc_sig"], strict=True)])
        w = 1.0 / np.maximum(p, 0.05)
    for m, pred in oof.items():
        err = D.censor_err(y, pred, c)
        mae, lo, hi = D.grouped_boot(err, g, seed=seed)
        unc = ~c
        rec = {"mae": mae, "ci": [lo, hi],
               "rmse_uncensored": float(np.sqrt(np.mean((pred[unc] - y[unc]) ** 2))),
               "spearman_uncensored": float(pd.Series(pred[unc]).corr(pd.Series(y[unc]), method="spearman"))}
        if w is not None:
            wm, wl, wh = D.grouped_boot(err, g, seed=seed, weights=w)
            rec["ips_mae"], rec["ips_ci"] = wm, [wl, wh]
        out[m] = rec
    # paired differences (card U)
    def paired(a, b):
        ea, eb = D.censor_err(y, oof[a], c), D.censor_err(y, oof[b], c)
        mean, lo, hi = D.grouped_boot(ea - eb, g, seed=seed)
        return {"diff": mean, "ci": [lo, hi], "excludes_zero_positive": lo > 0}
    out["_paired"] = {"D5-noproc minus D5 (H2)": paired("D5-noproc", "D5"),
                      "D7-noproc minus D7 (H2)": paired("D7-noproc", "D7"),
                      "D5 minus D7 (D7 promotion)": paired("D5", "D7"),
                      "D4 minus D5": paired("D4", "D5")}
    out["_groups"] = int(len(np.unique(g)))
    return out


def main(argv):
    quick = "--quick" in argv
    card_sha = check_prereg()
    cells = D.load_cells(ROOT / "ledgers/evidence/evidence_v0.jsonl").reset_index(drop=True)
    cluster = D.duplicate_clusters(cells)
    n_dup = sum(1 for c, cid in cluster.items() if c != cid)
    dup_clusters = len({cid for c, cid in cluster.items() if c != cid})
    leakage = {"codes": len(cluster), "codes_in_duplicate_clusters": n_dup + dup_clusters,
               "duplicate_clusters": dup_clusters}
    prop1, prop2 = D.propensity(cells, False), D.propensity(cells, True)
    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ("-quick" if quick else "")
    out_dir = ROOT / "experiments/DEL2/runs" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {"card_sha256": card_sha, "quick": quick, "cells": len(cells),
               "censored_share": float(cells["censored"].mean()), "leakage_audit": leakage,
               "propensity": {"spec1": {k: v for k, v in prop1.items() if k != "p_of"},
                              "spec2_interaction": {k: v for k, v in prop2.items() if k != "p_of"}},
               "splits": {}}
    seeds = D.SEEDS[:1] if quick else D.SEEDS
    for split in ("pair", "ingredient", "process", "random"):
        results["splits"][split] = {}
        for seed in seeds:
            oof, conf, chosen, folds = run(cells, cluster, split, seed, quick)
            summ = summarise(cells, oof, split, cluster, seed, prop1 if split in ("pair", "ingredient") else None)
            summ["_conformal"] = {m: {"coverage_mean": float(np.mean([f["coverage"] for f in v])),
                                      "width_mean": float(np.mean([f["width"] for f in v])), "folds": v}
                                  for m, v in conf.items()}
            summ["_hyperparams"] = chosen
            results["splits"][split][str(seed)] = summ
            pd.DataFrame({**{m: p for m, p in oof.items()}, "fold": folds}).assign(
                code=cells["code"], nutrient=cells["nutrient"], y=cells["y"], censored=cells["censored"]
            ).to_parquet(out_dir / f"oof_{split}_{seed}.parquet", index=False)
            print(f"[{split} seed {seed}] " + "  ".join(
                f"{m}={summ[m]['mae']:.2f}" for m in ("D0", "D1", "D2", "D3", "D4", "D5", "D5-noproc", "D7", "D7-noproc", "MF-biased")))
    # ---- card R: negative control — permute process labels across codes within food group
    rng = np.random.default_rng(D.SEEDS[0])
    codes = cells.drop_duplicates("code")[["code", "food_group", "procs", "proc_sig", "proc_fams"]].copy()
    perm = codes.groupby("food_group", group_keys=False).apply(
        lambda g: g.assign(**{c: rng.permutation(g[c].to_numpy()) for c in ("procs", "proc_sig", "proc_fams")}))
    neg = cells.drop(columns=["procs", "proc_sig", "proc_fams"]).merge(
        perm[["code", "procs", "proc_sig", "proc_fams"]], on="code", how="left")
    # (column order differs but every function selects columns by name)
    oof_n, _, _, _ = run(neg, cluster, "pair", D.SEEDS[0], True)
    yn, cn = neg["y"].to_numpy(), neg["censored"].to_numpy()
    gn = D.group_ids(neg, "pair", cluster).to_numpy()
    dn = D.grouped_boot(D.censor_err(yn, oof_n["D5-noproc"], cn) - D.censor_err(yn, oof_n["D5"], cn), gn, seed=1)
    results["negative_control"] = {"D5-noproc minus D5 under permuted processes": {"diff": dn[0], "ci": [dn[1], dn[2]]},
                                   "expectation": "advantage of process features disappears (CI includes 0 or ≤ 0)"}
    # ---- card S: positive control — inject −20 points into every cell whose processes include boil
    pos = cells.copy()
    hit = pos["procs"].str.contains("PROC-boil", regex=False)
    pos.loc[hit, "y"] = pos.loc[hit, "y"] - 20.0
    pos.loc[hit, "censored"] = False
    oof_o, _, _, fo = run(cells, cluster, "pair", D.SEEDS[0], True)
    oof_p, _, _, _ = run(pos, cluster, "pair", D.SEEDS[0], True)
    rec = float(np.mean(oof_p["D5"][hit.to_numpy()] - oof_o["D5"][hit.to_numpy()]))
    rec_other = float(np.mean(oof_p["D5"][~hit.to_numpy()] - oof_o["D5"][~hit.to_numpy()]))
    results["positive_control"] = {"injected_effect": -20.0, "recovered_on_boil_cells": rec,
                                   "spillover_on_other_cells": rec_other, "boil_cells": int(hit.sum())}
    print("negative control:", results["negative_control"])
    print("positive control:", results["positive_control"])
    (out_dir / "metrics.json").write_text(json.dumps(results, indent=2))
    print("wrote", out_dir.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
