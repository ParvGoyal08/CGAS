r"""
P15 — B15 bounded chain (v4.0 AH12): rank-frequency / null fit on the A1 corpus.

    .venv/bin/python tools/run_b15_rankfreq.py [n_boot]

Data: A1 deliverable Q1c_recipe_ingredient.csv (11,934 recipes; our own course corpus, used
locally). Step 2 (Kinouchi copy–mutate reproduction) is BLOCKED until the original paper is
obtained (SSOT §261.18 #1) — not attempted from secondary notation.

Null: Q2(a)-style size-preserving uniform cuisine (A2 control; reuses classical.core sampler).
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import sys
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from culinarystate.classical.core import assert_binary_membership, sample_without_replacement  # noqa: E402
from culinarystate.evolution.csn import compare_all, fit_alternatives, fit_power_law, gof_pvalue, heaps  # noqa: E402

A1 = ROOT.parents[1] / "A1/outputs/Q1/Q1c_recipe_ingredient.csv"
OUT = ROOT / "experiments/B15/rankfreq_v0"
SEED = 20261008


def load():
    per = defaultdict(set)
    with A1.open(encoding="utf-8") as fh:
        r = csv.reader(fh)
        next(r)
        for rid, ing in r:
            per[rid].add(ing)
    baskets = [sorted(per[k]) for k in sorted(per)]
    assert_binary_membership(baskets)
    return baskets


def analyse(freqs: np.ndarray, n_boot: int, seed: int) -> dict:
    f = fit_power_law(freqs)
    alts = fit_alternatives(freqs, f.xmin)
    return {"xmin": f.xmin, "alpha": f.alpha, "alpha_at_optimizer_bound": bool(f.alpha > 5.99 or f.alpha < 1.001), "alpha_se": f.alpha_se, "ks": f.ks, "n_tail": f.n_tail, "n": f.n,
            "gof_p": gof_pvalue(freqs, f, n_boot, seed) if n_boot else None, "n_boot": n_boot,
            "params": {k: v["params"] for k, v in alts.items()},
            "loglik": {k: float(v["ll"].sum()) for k, v in alts.items()},
            "comparisons": compare_all(alts)}


def main() -> int:
    n_boot = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    OUT.mkdir(parents=True, exist_ok=True)
    baskets = load()
    vocab = sorted({i for b in baskets for i in b})
    idx = {v: k for k, v in enumerate(vocab)}
    real = np.array(sorted(Counter(i for b in baskets for i in b).values(), reverse=True))
    rng = np.random.default_rng(SEED)
    sizes = np.array([len(b) for b in baskets])
    null = sample_without_replacement(sizes, np.ones(len(vocab)), rng)
    nullf = np.bincount(np.concatenate(null), minlength=len(vocab))
    nullf = np.sort(nullf[nullf > 0])[::-1]
    res = {"input": {"path": str(A1.relative_to(ROOT.parents[1])), "sha256": hashlib.sha256(A1.read_bytes()).hexdigest(),
                     "recipes": len(baskets), "ingredients": len(vocab), "memberships": int(sizes.sum())},
           "method": "Clauset-Shalizi-Newman 2009; discrete MLE; KS xmin; semi-parametric bootstrap with CSN eq. D.6 tail sampler (approximation); Vuong for non-nested; chi2_1 for PL vs truncated PL",
           "real": analyse(real, n_boot, SEED),
           "null_q2a_uniform": analyse(nullf, 0, SEED),
           "null_note": "one Q2(a) size-preserving uniform cuisine; GoF bootstrap not run on the null (descriptive contrast only). "
                        "The Q3 frequency-weighted null reproduces f_i by construction and is NOT a test of the tail.",
           "heaps": heaps([[idx[i] for i in b] for b in baskets], n_perm=20, seed=SEED),
           "kinouchi_reproduction": "BLOCKED: original paper (Kinouchi et al. 2008, NJP 10 073020) not yet obtained; SSOT §261.18 #1 forbids reconstruction from secondary notation"}
    (OUT / "results.json").write_text(json.dumps(res, indent=2))
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
    for f, lab in ((real, "A1 corpus"), (nullf, "Q2(a) uniform null")):
        ax[0].loglog(np.arange(1, len(f) + 1), f, ".", ms=2, label=lab)
        u, c = np.unique(f, return_counts=True)
        ccdf = 1 - np.concatenate([[0], np.cumsum(c)[:-1]]) / c.sum()
        ax[1].loglog(u, ccdf, ".", ms=3, label=lab)
    r = res["real"]
    xs = np.unique(real[real >= r["xmin"]]).astype(float)
    from scipy import special
    tailfrac = r["n_tail"] / r["n"]
    ax[1].loglog(xs, tailfrac * special.zeta(r["alpha"], xs) / special.zeta(r["alpha"], r["xmin"]), "k-", lw=1,
                 label=f"PL fit α={r['alpha']:.2f}, xmin={r['xmin']}")
    ax[0].set(xlabel="rank", ylabel="recipes containing ingredient", title="Rank–frequency (descriptive)")
    ax[1].set(xlabel="frequency f", ylabel="P(F ≥ f)", title="CCDF + discrete MLE power-law tail")
    h = res["heaps"]
    ax[2].plot(h["n"], h["V_mean"], "-")
    ax[2].fill_between(h["n"], np.array(h["V_mean"]) - h["V_sd"], np.array(h["V_mean"]) + h["V_sd"], alpha=.3)
    ax[2].set(xlabel="recipes seen (random order)", ylabel="distinct ingredients", title="Vocabulary growth (Heaps-type)")
    for a in ax[:2]:
        a.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "rankfreq.png", dpi=130)
    print(json.dumps({k: v for k, v in res["real"].items() if k != "params"}, indent=1))
    print("null:", {k: res["null_q2a_uniform"][k] for k in ("xmin", "alpha", "n_tail")},
          {k: v["favours"] for k, v in res["null_q2a_uniform"]["comparisons"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
