r"""
K15 — B03-lite: frozen Level-7/8 statistics as a tested library (v4.0 AH8, AQ1).

SSOT anchors (frozen):
  §80  n_ij = |F_i ∩ F_j|;  N_s(R) = 2/(n_R(n_R−1)) · Σ_{i<j∈R} n_ij;  N̄_s(C) = mean_R N_s(R)
  §81  four null cuisines, all preserving recipe size:
       uniform · ingredient-frequency · ingredient-category · category + frequency
  §82  Monte-Carlo protocol: record M, seed, size rule, universe, weights, category map,
       number of random recipes, duplicate policy — no Z from an undocumented generator

The weighted sampler is ported from Assignment 2 (`A2/src/random_controls.py`,
Efraimidis–Spirakis: key = Exp(1)/w, keep the k smallest), as SSOT §279.3 directs.
Binary membership: a recipe is a SET of ingredients (A2 invariant).
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Hashable, Optional

import numpy as np


# ------------------------------------------------------------------ invariants
def assert_binary_membership(recipes: list) -> None:
    for k, r in enumerate(recipes):
        if len(r) != len(set(r)):
            raise ValueError(f"recipe {k} repeats an ingredient (membership must be binary)")


# ------------------------------------------------------------------ §80
def n_ij(Fi: set, Fj: set) -> int:
    return len(Fi & Fj)


def N_s_recipe(recipe, profiles: dict[Hashable, set]) -> Optional[float]:
    """Mean shared compounds over ingredient pairs. None for n_R < 2 (undefined)."""
    ings = [i for i in recipe if i in profiles]
    n = len(ings)
    if n < 2:
        return None
    tot = sum(n_ij(profiles[a], profiles[b]) for a, b in itertools.combinations(ings, 2))
    return 2.0 * tot / (n * (n - 1))


def N_s_cuisine(recipes, profiles) -> float:
    vals = [v for v in (N_s_recipe(r, profiles) for r in recipes) if v is not None]
    return float(np.mean(vals)) if vals else float("nan")


# ------------------------------------------------------------------ A2 sampler (ported)
def sample_without_replacement(sizes: np.ndarray, weights: np.ndarray, rng: np.random.Generator,
                               chunk: int = 4000) -> list[np.ndarray]:
    """For each size k draw k DISTINCT item indices with probability ∝ weights (Efraimidis–Spirakis)."""
    n_items = len(weights)
    w = np.asarray(weights, dtype=np.float64)
    if (w <= 0).any():
        raise ValueError("weights must be positive")
    w = w / w.sum()
    out: list = [None] * len(sizes)
    for k in np.unique(sizes):
        rows = np.flatnonzero(sizes == k)
        k = int(k)
        if k > n_items:
            raise ValueError(f"recipe size {k} exceeds universe {n_items}")
        for start in range(0, len(rows), chunk):
            block = rows[start:start + chunk]
            keys = rng.exponential(size=(len(block), n_items)) / w
            part = np.argpartition(keys, k - 1, axis=1)[:, :k] if k < n_items else np.tile(np.arange(n_items), (len(block), 1))
            for r, row_idx in enumerate(block):
                out[row_idx] = np.sort(part[r])
    return out


# ------------------------------------------------------------------ §81 null cuisines
@dataclass
class NullSpec:
    kind: str                                     # uniform | frequency | category | category_frequency | swap
    universe: list
    frequency: Optional[dict] = None              # ingredient → count (frequency kinds)
    category: Optional[dict] = None               # ingredient → category (category kinds)
    notes: dict = field(default_factory=dict)


def null_cuisine(recipes: list, spec: NullSpec, rng: np.random.Generator) -> list[list]:
    sizes = np.array([len(r) for r in recipes])
    uni = list(spec.universe)
    if spec.kind in ("uniform", "frequency"):
        w = np.ones(len(uni)) if spec.kind == "uniform" else np.array([spec.frequency[x] for x in uni], float)
        draws = sample_without_replacement(sizes, w, rng)
        return [[uni[j] for j in d] for d in draws]
    if spec.kind in ("category", "category_frequency"):
        by_cat: dict = {}
        for x in uni:
            by_cat.setdefault(spec.category[x], []).append(x)
        out = []
        for r in recipes:
            new, used = [], set()
            for ing in r:
                pool = [x for x in by_cat[spec.category[ing]] if x not in used]
                if not pool:
                    raise ValueError(f"category {spec.category[ing]} too small for a recipe")
                if spec.kind == "category":
                    pick = pool[int(rng.integers(len(pool)))]
                else:
                    p = np.array([spec.frequency[x] for x in pool], float)
                    pick = pool[int(rng.choice(len(pool), p=p / p.sum()))]
                new.append(pick)
                used.add(pick)
            out.append(new)
        return out
    if spec.kind == "swap":
        return curveball(recipes, rng, trades=spec.notes.get("trades"))
    raise ValueError(f"unknown null kind {spec.kind}")


def curveball(recipes: list, rng: np.random.Generator, trades: Optional[int] = None) -> list[list]:
    """Degree-preserving randomisation (Strona et al. 2014, 'curveball'): repeatedly pick two
    recipes, pool the ingredients each has that the other lacks, shuffle, and hand back the same
    number to each. Recipe sizes AND ingredient frequencies f_i are preserved EXACTLY; only
    co-occurrence structure is randomised. (The 'frequency' null is frequency-WEIGHTED and does not
    preserve f_i exactly — it leaves part of a popularity artefact; see test_classical_confounds.)"""
    rs = [set(r) for r in recipes]
    n = len(rs)
    trades = trades if trades is not None else 5 * n
    for _ in range(trades):
        a, b = rng.choice(n, 2, replace=False)
        only_a, only_b = rs[a] - rs[b], rs[b] - rs[a]
        if not only_a or not only_b:
            continue
        pool = list(only_a | only_b)
        rng.shuffle(pool)
        k = len(only_a)
        common = rs[a] & rs[b]
        rs[a] = common | set(pool[:k])
        rs[b] = common | set(pool[k:])
    return [sorted(r) for r in rs]


# ------------------------------------------------------------------ §82 Monte Carlo
@dataclass
class MonteCarloResult:
    real: float
    null_mean: float
    null_sd: float
    delta: float          # ΔN_s = N̄_s(real) − ⟨N̄_s(null)⟩
    z: float              # (real − mean) / sd
    p_emp_upper: float    # (1 + #{null ≥ real}) / (1 + M)
    record: dict          # §82 documentation fields


def monte_carlo(recipes, profiles, spec: NullSpec, M: int, seed: int) -> MonteCarloResult:
    assert_binary_membership(recipes)
    rng = np.random.default_rng(seed)
    real = N_s_cuisine(recipes, profiles)
    sims = np.array([N_s_cuisine(null_cuisine(recipes, spec, rng), profiles) for _ in range(M)])
    mu, sd = float(sims.mean()), float(sims.std(ddof=1)) if M > 1 else float("nan")
    return MonteCarloResult(
        real, mu, sd, real - mu, (real - mu) / sd if sd and sd > 0 else float("nan"),
        float((1 + (sims >= real).sum()) / (1 + M)),
        {"M": M, "seed": seed, "size_rule": "each random recipe copies one real recipe's size",
         "universe_size": len(spec.universe), "null": spec.kind,
         "weights": "observed frequencies" if spec.kind in ("frequency", "category_frequency") else "uniform",
         "category_map": spec.category is not None, "random_recipes_per_sim": len(recipes),
         "duplicate_policy": "no repeated ingredient within a recipe (sampling without replacement)"})


# ------------------------------------------------------------------ A2 regression helpers
def size_hist(recipes) -> dict[int, int]:
    h: dict[int, int] = {}
    for r in recipes:
        h[len(r)] = h.get(len(r), 0) + 1
    return dict(sorted(h.items()))


def frequency(recipes) -> dict:
    f: dict = {}
    for r in recipes:
        for i in set(r):
            f[i] = f.get(i, 0) + 1
    return f
