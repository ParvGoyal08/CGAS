r"""
T07 — Kinouchi et al. (2008, NJP 10 073020) copy–mutate model, reimplemented from the source card
(research/briefs/L13E-kinouchi2008-card.md §5). Every choice the paper leaves open is an explicit
argument named after its ambiguity id (A1…A21); defaults = the PROPOSED primary choices in
experiments/B15/kinouchi_v0/prereg.md. Nothing here is run at paper scale until that file is frozen.

Paper symbols: T (stop), K (recipe size), L (mutation attempts), M (pool/recipe ratio), R0 (initial recipes).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Config:
    T: int = 1200
    K: int = 11
    L: int = 4
    M: int = 3
    R0: int = 20
    initial: str = "IC-a"            # A1/A2: "IC-a" pool M·R0, recipes drawn from it | "IC-b" K·R0 distinct founders
    stop: str = "R_equals_T"         # A3: "R_equals_T" (T−R0 steps) | "T_steps"
    loci: str = "with_replacement"   # A4: positions drawn independently each repeat | "without_replacement"
    duplicate: str = "reject"        # A6: j already in the daughter → no replacement | "allow"
    selection: str = "fitness"       # A21: "fitness" (replace iff f_j > f_i) | "always" (ablation)


@dataclass
class Result:
    recipes: list                    # each: np.ndarray of K ingredient ids (with "allow" duplicates may repeat)
    fitness: np.ndarray              # fitness of every pool ingredient (index = id)
    founders: set                    # ingredient ids present in the R0 initial recipes
    pool_sizes: list = field(default_factory=list)
    total_fitness: list = field(default_factory=list)   # F_Total(R(t)) after each step


def simulate(cfg: Config, seed: int) -> Result:
    rng = np.random.default_rng(seed)
    if cfg.initial == "IC-a":
        pool = cfg.M * cfg.R0
        if cfg.K > pool:
            raise ValueError("K exceeds the initial pool under IC-a")
        fit = list(rng.random(pool))                                          # A7: U[0,1]
        recipes = [rng.choice(pool, cfg.K, replace=False) for _ in range(cfg.R0)]
    elif cfg.initial == "IC-b":
        pool = cfg.K * cfg.R0
        fit = list(rng.random(pool))
        recipes = [np.arange(r * cfg.K, (r + 1) * cfg.K) for r in range(cfg.R0)]
    else:
        raise ValueError(cfg.initial)
    founders = {int(i) for r in recipes for i in r}
    steps = cfg.T - cfg.R0 if cfg.stop == "R_equals_T" else cfg.T
    res = Result([], np.empty(0), founders)
    # each recipe's mean fitness is fixed once the recipe exists (ingredient fitness never changes),
    # so F_Total is a running mean of per-recipe means — identical to recomputing it, and O(1) per step
    mean_sum = float(sum(np.mean([fit[int(i)] for i in r]) for r in recipes))
    for _ in range(steps):
        mother = recipes[int(rng.integers(len(recipes)))]                    # A9: uniform over all recipes
        d = mother.copy()
        positions = (rng.integers(cfg.K, size=cfg.L) if cfg.loci == "with_replacement"
                     else rng.choice(cfg.K, size=min(cfg.L, cfg.K), replace=False))
        n_pool = len(fit)
        for pos in positions:                                                 # A10: sequential on the copy
            j = int(rng.integers(n_pool))                                     # A5: uniform over the whole pool
            if cfg.duplicate == "reject" and j in d:
                continue
            if cfg.selection == "always" or fit[j] > fit[int(d[pos])]:
                d[pos] = j
        recipes.append(d)
        target = cfg.M * len(recipes)                                         # A8: grow after the daughter
        if target > len(fit):
            fit.extend(rng.random(target - len(fit)))
        res.pool_sizes.append(len(fit))
        mean_sum += float(np.mean([fit[int(i)] for i in d]))
        res.total_fitness.append(mean_sum / len(recipes))
    res.recipes, res.fitness = recipes, np.asarray(fit)
    return res


def rank_frequency(res: Result) -> np.ndarray:
    """A12: f(r) = fraction of ALL recipes (incl. founders) containing the rank-r ingredient;
    never-used ingredients excluded; counting = number of recipes containing (published rule)."""
    counts = {}
    for r in res.recipes:
        for i in set(int(x) for x in r):
            counts[i] = counts.get(i, 0) + 1
    return np.sort(np.array(list(counts.values()), dtype=float))[::-1] / len(res.recipes)
