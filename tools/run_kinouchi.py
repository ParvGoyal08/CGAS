r"""
T07 — run the Kinouchi copy–mutate reproduction exactly as pre-registered.
    .venv/bin/python tools/run_kinouchi.py
Frozen: experiments/B15/kinouchi_v0/prereg.md (sha in FREEZE.md / registry/preregistration.csv);
pre-run clarifications C1–C7: experiments/B15/kinouchi_v0/clarifications_prerun.md.
Refuses to run if the frozen file's hash changed. Writes experiments/B15/kinouchi_v0/results/.
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import sys
from dataclasses import replace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from culinarystate.evolution.csn import compare_all, fit_alternatives, fit_power_law, gof_pvalue  # noqa: E402
from culinarystate.evolution.kinouchi import Config, rank_frequency, simulate  # noqa: E402

EXP = ROOT / "experiments/B15/kinouchi_v0"
OUT = EXP / "results"
SEEDS = [20261008 + s for s in range(5)]
C, A, BETA, RC = 8.7, 6.4, 1.31, 800.0                       # published eq. (1) (A14)


def check_freeze():
    reg = {r["experiment"]: r for r in csv.DictReader((ROOT / "registry/preregistration.csv").open())}
    want = reg["B15-KINOUCHI-REPRO"]["sha256"]
    got = hashlib.sha256((EXP / "prereg.md").read_bytes()).hexdigest()
    if want != got:
        raise SystemExit("prereg.md changed after freeze — refusing to run")
    return got


def eq1(r):
    return C / (A + r) ** BETA * np.exp(-r / RC)


def seed_mean(curves):
    L = min(len(c) for c in curves)
    return np.mean([c[:L] for c in curves], axis=0)


def ac1(f):
    r = np.arange(1, min(500, len(f)) + 1)
    within = np.abs(np.log10(f[: len(r)]) - np.log10(eq1(r))) <= 0.2
    return {"share_within_0.2_decade": float(within.mean()), "ranks_compared": int(len(r)), "pass": bool(within.mean() >= 0.9)}


def ac2(series_list, R0):
    y = 1 - np.mean(series_list, axis=0)
    t = np.arange(R0 + 1, R0 + 1 + len(y))
    k = int(np.argmax(y))
    rises = k > 0 and y[-1] < y[k]
    out = {"argmax_t": int(t[k]), "rises_then_decays": bool(rises)}
    if rises and len(y) - k >= 3:
        slope, icpt = np.polyfit(np.log(t[k:]), np.log(y[k:]), 1)
        pred = slope * np.log(t[k:]) + icpt
        ss = ((np.log(y[k:]) - pred) ** 2).sum()
        sst = ((np.log(y[k:]) - np.log(y[k:]).mean()) ** 2).sum()
        out.update(gamma=float(-slope), r2=float(1 - ss / sst))
    else:
        out.update(gamma=None, r2=None)
    out["pass"] = bool(rises and out["gamma"] is not None and 0.05 <= out["gamma"] <= 0.2)
    return out


def ranked_ingredients(res):
    counts = {}
    for r in res.recipes:
        for i in set(int(x) for x in r):
            counts[i] = counts.get(i, 0) + 1
    return sorted(counts, key=lambda i: (-counts[i], i)), counts


def ac3_one(res, cfg):
    order, _ = ranked_ingredients(res)
    f = res.fitness
    a = float(np.mean(f[order])) > 0.5
    kr0 = cfg.K * cfg.R0
    b = any(i in res.founders and f[i] < 0.2 for i in order[:kr0])
    c = any(f[i] > 0.8 for i in order[500:])
    return {"a_mean_fitness_gt_0.5": a, "b_low_fitness_founder_top": b, "c_high_fitness_low_rank": c, "all": a and b and c}


def founder_share(res, cfg):
    order, _ = ranked_ingredients(res)
    top = order[: cfg.K * cfg.R0]
    return sum(i in res.founders for i in top) / len(top)


def ac5(res, cfg):
    R = len(res.recipes)
    expect_R = cfg.T if cfg.stop == "R_equals_T" else cfg.T + cfg.R0
    pool_ok = all(p == max(cfg.M * (cfg.R0 + i + 1), cfg.K * cfg.R0 if cfg.initial == "IC-b" else 0)
                  for i, p in enumerate(res.pool_sizes))
    return {"R_equals_expected": R == expect_R, "pool_rule": pool_ok, "K_slots": all(len(x) == cfg.K for x in res.recipes),
            "pass": R == expect_R and pool_ok and all(len(x) == cfg.K for x in res.recipes)}


def main() -> int:
    sha = check_freeze()
    OUT.mkdir(parents=True, exist_ok=True)
    base = Config()
    variants = {"primary": base, "IC-b": replace(base, initial="IC-b"), "A3_T_steps": replace(base, stop="T_steps"),
                "A4_without_replacement": replace(base, loci="without_replacement"),
                "N1_no_selection": replace(base, selection="always")}
    runs = {v: [simulate(cfg, s) for s in SEEDS] for v, cfg in variants.items()}
    res = {"prereg_sha256": sha, "seeds": SEEDS, "variants": {}}
    for v, cfg in variants.items():
        rs = runs[v]
        fs = [rank_frequency(r) for r in rs]
        a3 = [ac3_one(r, cfg) for r in rs]
        res["variants"][v] = {
            "config": cfg.__dict__, "AC1": ac1(seed_mean(fs)), "AC2": ac2([r.total_fitness for r in rs], cfg.R0),
            "AC2_per_seed_gamma": [ac2([r.total_fitness], cfg.R0)["gamma"] for r in rs],
            "AC3": {"per_seed": a3, "pass": sum(x["all"] for x in a3) >= 4},
            "AC5": {"per_seed": [ac5(r, cfg) for r in rs], "pass": all(ac5(r, cfg)["pass"] for r in rs)},
            "founder_share_top_KR0": float(np.mean([founder_share(r, cfg) for r in rs])),
            "used_ingredients_mean": float(np.mean([len(f) for f in fs]))}
    p, n1 = res["variants"]["primary"], res["variants"]["N1_no_selection"]
    res["AC4"] = {"with_selection": p["founder_share_top_KR0"], "without_selection": n1["founder_share_top_KR0"],
                  "pass": n1["founder_share_top_KR0"] > p["founder_share_top_KR0"]}
    res["overall"] = "REPRODUCED (bounded)" if (p["AC1"]["pass"] and p["AC2"]["pass"] and p["AC5"]["pass"]) else "NOT REPRODUCED"
    # N2 null: T recipes of K uniform-without-replacement draws from the primary seed-0 final pool
    r0 = runs["primary"][0]
    rng = np.random.default_rng(SEEDS[0])
    pool = len(r0.fitness)
    n2 = type(r0)([rng.choice(pool, base.K, replace=False) for _ in range(base.T)], r0.fitness, set())
    f_n2 = rank_frequency(n2)
    # T2 heavy-tail table on seed-0 primary counts
    _, counts = ranked_ingredients(r0)
    x = np.array(sorted(counts.values(), reverse=True))
    fit = fit_power_law(x, min_tail=30)
    alts = fit_alternatives(x, fit.xmin)
    res["T2_heavy_tail_seed0"] = {"xmin": fit.xmin, "alpha": fit.alpha, "ks": fit.ks, "n_tail": fit.n_tail,
                                  "gof_p_1000": gof_pvalue(x, fit, 1000, SEEDS[0], min_tail=30),
                                  "comparisons": compare_all(alts)}
    (OUT / "results.json").write_text(json.dumps(res, indent=2, default=str))
    # ---- figures
    fp = seed_mean([rank_frequency(r) for r in runs["primary"]])
    fn1 = seed_mean([rank_frequency(r) for r in runs["N1_no_selection"]])
    fig, ax = plt.subplots(figsize=(8, 5))
    rr = np.arange(1, len(fp) + 1)
    lo = np.min([rank_frequency(r)[: len(fp)] for r in runs["primary"]], axis=0)
    hi = np.max([rank_frequency(r)[: len(fp)] for r in runs["primary"]], axis=0)
    ax.fill_between(rr, lo, hi, alpha=0.25, label="primary: min–max over 5 seeds")
    ax.loglog(rr, fp, lw=2, label="primary: 5-seed mean")
    ax.loglog(rr, eq1(rr), "k--", lw=1.5, label="published eq. (1)")
    ax.loglog(np.arange(1, len(fn1) + 1), fn1, lw=1, label="N1: no selection")
    ax.loglog(np.arange(1, len(f_n2) + 1), f_n2, lw=1, label="N2: uniform size-controlled")
    ax.axvline(500, color="grey", lw=0.8, ls=":")
    ax.set(xlabel="rank r", ylabel="f(r) = share of recipes containing the ingredient", title="F1 Kinouchi model vs published eq. (1)")
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "F1_rank_frequency.png", dpi=150); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 5))
    for r in runs["primary"]:
        t = np.arange(base.R0 + 1, base.R0 + 1 + len(r.total_fitness))
        ax.loglog(t, 1 - np.asarray(r.total_fitness), lw=0.8, alpha=0.7)
    ax.set(xlabel="t = number of recipes", ylabel="1 − F_Total(t)", title=f"F2 cuisine fitness gap (γ_mean = {p['AC2']['gamma']})")
    fig.tight_layout(); fig.savefig(OUT / "F2_fitness_gap.png", dpi=150); plt.close(fig)
    order, _ = ranked_ingredients(r0)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(np.arange(1, len(order) + 1), r0.fitness[order], s=4, label="ingredient")
    fo = [k + 1 for k, i in enumerate(order) if i in r0.founders]
    ax.scatter(fo, r0.fitness[[order[k - 1] for k in fo]], s=14, c="red", label="founder")
    ax.set(xscale="log", xlabel="rank r", ylabel="fitness f", title="F3 fitness vs rank (primary, seed 0)")
    ax.legend(); fig.tight_layout(); fig.savefig(OUT / "F3_fitness_vs_rank.png", dpi=150); plt.close(fig)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(["with selection", "without selection"], [res["AC4"]["with_selection"], res["AC4"]["without_selection"]])
    ax.set(ylabel="founder share of ranks 1…K·R0", title="F4 founder effect")
    fig.tight_layout(); fig.savefig(OUT / "F4_founder_share.png", dpi=150); plt.close(fig)
    # ---- T1 table
    lines = ["# T07 Kinouchi reproduction — results", "",
             f"Pre-registration sha256 `{sha[:16]}…` (frozen; checked before run). Seeds {SEEDS}.", "",
             f"**Overall (pre-registered rule: AC-1, AC-2, AC-5 under primary): {res['overall']}**", "",
             "| Variant | AC-1 share ≤0.2 dec (pass ≥0.9) | AC-2 γ (pass 0.05–0.2) / rises-then-decays | AC-3 (≥4/5 seeds) | AC-5 |", "|---|---|---|---|---|"]
    for v, d in res["variants"].items():
        g = d["AC2"]["gamma"]
        lines.append(f"| {v} | {d['AC1']['share_within_0.2_decade']:.3f} {'PASS' if d['AC1']['pass'] else 'FAIL'} | "
                     f"{'—' if g is None else f'{g:.3f}'} / {d['AC2']['rises_then_decays']} {'PASS' if d['AC2']['pass'] else 'FAIL'} | "
                     f"{sum(x['all'] for x in d['AC3']['per_seed'])}/5 {'PASS' if d['AC3']['pass'] else 'FAIL'} | {'PASS' if d['AC5']['pass'] else 'FAIL'} |")
    a4 = res["AC4"]
    t2 = res["T2_heavy_tail_seed0"]
    lines += ["", f"**AC-4** founder share of ranks 1…K·R0: with selection {a4['with_selection']:.3f}, without {a4['without_selection']:.3f} → {'PASS' if a4['pass'] else 'FAIL'}", "",
              "**T2 heavy tail (seed 0, primary; descriptive):** "
              f"xmin {t2['xmin']}, α {t2['alpha']:.3f}, KS {t2['ks']:.3f}, bootstrap p {t2['gof_p_1000']:.3f}; "
              + "; ".join(f"{k}: {v['favours']}" for k, v in t2["comparisons"].items()), "",
              "Figures: F1_rank_frequency.png, F2_fitness_gap.png, F3_fitness_vs_rank.png, F4_founder_share.png.", "",
              "No threshold, range, seed or variant was changed after the run (prereg 'No post-result changes')."]
    (OUT / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
