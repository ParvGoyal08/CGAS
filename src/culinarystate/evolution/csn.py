r"""
P15 — B15 bounded chain, step 1: principled heavy-tail model comparison
(Clauset, Shalizi & Newman 2009, SIAM Review 51:661; v4.0 Part M §4 — "never a straight
line on a log-log plot").

Data are DISCRETE counts x ≥ 1 (e.g. f_i = number of recipes containing ingredient i).

  power law          p(x) = x^-α / ζ(α, xmin)                          x ≥ xmin
  exponential        p(x) = (1 - e^-λ) e^{-λ (x - xmin)}
  lognormal          p(x) ∝ exp(-(ln x - μ)² / 2σ²) / x                 (normalised numerically)
  truncated PL       p(x) ∝ x^-α e^{-λx}                               (normalised numerically)

  xmin    : minimises the KS distance between the tail and the fitted power law (CSN §3.3)
  GoF     : semi-parametric bootstrap p-value (CSN §4.1); p < 0.1 rejects the power law
  compare : Vuong normalised log-likelihood ratio for non-nested pairs (CSN §5);
            for PL vs truncated PL (nested) the likelihood-ratio p uses χ²₁ (Wilks), as CSN Table 6.

Tail sampling in the bootstrap uses CSN eq. D.6 (discrete approximation) — recorded as an
approximation in every output.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import optimize, special, stats

NORM_UPPER = 10**6          # numerical normalisation upper bound for lognormal / truncated PL


def _pl_alpha(x: np.ndarray, xmin: int) -> tuple[float, float]:
    sl = np.log(x).sum()
    n = len(x)
    f = lambda a: n * np.log(special.zeta(a, xmin)) + a * sl
    r = optimize.minimize_scalar(f, bounds=(1.0001, 6.0), method="bounded", options={"xatol": 1e-6})
    return float(r.x), float(-r.fun)


def _pl_ks(x: np.ndarray, xmin: int, a: float) -> float:
    xs = np.sort(x)
    u = np.unique(xs)
    emp = np.searchsorted(xs, u, side="right") / len(xs)
    model = 1 - special.zeta(a, u + 1) / special.zeta(a, xmin)
    return float(np.max(np.abs(emp - model)))


@dataclass
class PLFit:
    xmin: int
    alpha: float
    alpha_se: float
    ks: float
    n_tail: int
    n: int


def fit_power_law(data, min_tail: int = 50) -> PLFit:
    data = np.asarray(data, dtype=np.int64)
    if (data < 1).any():
        raise ValueError("counts must be ≥ 1")
    best = None
    for xmin in np.unique(data):
        tail = data[data >= xmin]
        if len(tail) < min_tail:
            break
        a, _ = _pl_alpha(tail, int(xmin))
        ks = _pl_ks(tail, int(xmin), a)
        if best is None or ks < best[0]:
            best = (ks, int(xmin), a, len(tail))
    if best is None:
        raise ValueError("too few points for a tail fit")
    ks, xmin, a, nt = best
    return PLFit(xmin, a, (a - 1) / np.sqrt(nt), ks, nt, len(data))


def gof_pvalue(data, fit: PLFit, n_boot: int, seed: int, min_tail: int = 50) -> float:
    rng = np.random.default_rng(seed)
    data = np.asarray(data, dtype=np.int64)
    body = data[data < fit.xmin]
    ptail = fit.n_tail / fit.n
    worse = 0
    for _ in range(n_boot):
        k = rng.binomial(fit.n, ptail)
        u = rng.random(k)
        tail = np.floor((fit.xmin - 0.5) * (1 - u) ** (-1 / (fit.alpha - 1)) + 0.5).astype(np.int64)  # CSN D.6
        syn = np.concatenate([rng.choice(body, fit.n - k) if len(body) else np.empty(0, np.int64), tail])
        try:
            if fit_power_law(syn, min_tail).ks >= fit.ks:
                worse += 1
        except ValueError:
            continue
    return worse / n_boot


# ------------------------------------------------------------------ alternatives on the tail
def _ll_pl(x, xmin, a):
    return -a * np.log(x) - np.log(special.zeta(a, xmin))


def _ll_exp(x, xmin, lam):
    return np.log1p(-np.exp(-lam)) - lam * (x - xmin)


def _grid(xmin):
    return np.arange(xmin, NORM_UPPER + 1, dtype=np.float64)


def _ll_logn(x, xmin, mu, s, g=None):
    g = _grid(xmin) if g is None else g
    logw = -((np.log(g) - mu) ** 2) / (2 * s * s) - np.log(g)
    lz = special.logsumexp(logw)
    return -((np.log(x) - mu) ** 2) / (2 * s * s) - np.log(x) - lz


def _ll_tpl(x, xmin, a, lam, g=None):
    g = _grid(xmin) if g is None else g
    lz = special.logsumexp(-a * np.log(g) - lam * g)
    return -a * np.log(x) - lam * x - lz


def fit_alternatives(data, xmin: int) -> dict:
    x = np.asarray(data, dtype=np.float64)
    x = x[x >= xmin]
    g = _grid(xmin)
    out = {}
    a, _ = _pl_alpha(x.astype(np.int64), xmin)
    out["power_law"] = {"params": {"alpha": a}, "ll": _ll_pl(x, xmin, a)}
    r = optimize.minimize_scalar(lambda lam: -_ll_exp(x, xmin, lam).sum(), bounds=(1e-8, 10), method="bounded")
    out["exponential"] = {"params": {"lambda": float(r.x)}, "ll": _ll_exp(x, xmin, r.x)}
    lx = np.log(x)
    r = optimize.minimize(lambda p: -_ll_logn(x, xmin, p[0], np.exp(p[1]), g).sum(),
                          x0=[lx.mean(), np.log(max(lx.std(), 0.1))], method="Nelder-Mead",
                          options={"xatol": 1e-6, "fatol": 1e-6, "maxiter": 4000})
    out["lognormal"] = {"params": {"mu": float(r.x[0]), "sigma": float(np.exp(r.x[1]))},
                        "ll": _ll_logn(x, xmin, r.x[0], np.exp(r.x[1]), g)}
    r = optimize.minimize(lambda p: -_ll_tpl(x, xmin, p[0], np.exp(p[1]), g).sum(),
                          x0=[max(a - 0.1, 0.5), np.log(1e-4)], method="Nelder-Mead",
                          options={"xatol": 1e-7, "fatol": 1e-7, "maxiter": 4000})
    out["truncated_power_law"] = {"params": {"alpha": float(r.x[0]), "lambda": float(np.exp(r.x[1]))},
                                  "ll": _ll_tpl(x, xmin, r.x[0], np.exp(r.x[1]), g)}
    return out


def vuong(ll1: np.ndarray, ll2: np.ndarray) -> dict:
    d = ll1 - ll2
    R = float(d.sum())
    sd = float(d.std())
    p = float(special.erfc(abs(R) / (np.sqrt(2 * len(d)) * sd))) if sd > 0 else 1.0
    return {"R": R, "normalised_R": R / (np.sqrt(len(d)) * sd) if sd > 0 else 0.0, "p": p}


def compare_all(alts: dict) -> dict:
    pl = alts["power_law"]["ll"]
    out = {}
    for k in ("exponential", "lognormal"):
        v = vuong(pl, alts[k]["ll"])
        v["favours"] = ("power_law" if v["R"] > 0 else k) if v["p"] < 0.1 else "inconclusive"
        out[f"power_law_vs_{k}"] = v
    R = float((pl - alts["truncated_power_law"]["ll"]).sum())
    p = float(stats.chi2.sf(-2 * R, 1)) if R < 0 else 1.0
    out["power_law_vs_truncated_power_law"] = {"R": R, "p_nested_chi2_1": p,
                                               "favours": "truncated_power_law" if (R < 0 and p < 0.1) else "inconclusive"}
    return out


def heaps(baskets: list, n_perm: int, seed: int, points: int = 40) -> dict:
    """Vocabulary size V(n) after n recipes, mean ± sd over random orders."""
    rng = np.random.default_rng(seed)
    n = len(baskets)
    grid = np.unique(np.linspace(1, n, points).astype(int))
    curves = []
    for _ in range(n_perm):
        seen, j, cur = set(), 0, []
        order = rng.permutation(n)
        for i, idx in enumerate(order, start=1):
            seen.update(baskets[idx])
            if j < len(grid) and i == grid[j]:
                cur.append(len(seen))
                j += 1
        curves.append(cur)
    c = np.array(curves, dtype=float)
    beta, logk = np.polyfit(np.log(grid[grid >= n // 10]), np.log(c.mean(0)[grid >= n // 10]), 1)
    return {"n": grid.tolist(), "V_mean": c.mean(0).tolist(), "V_sd": c.std(0).tolist(),
            "heaps_beta_descriptive": float(beta),
            "note": "β is a descriptive log-log slope over the last 90% of recipes, not a fitted model"}
