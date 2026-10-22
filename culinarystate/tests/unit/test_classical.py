r"""K15 B03-lite regression tests: frozen L7/L8 statistics + the A2 null-model sampler."""
from __future__ import annotations

import numpy as np
import pytest

from culinarystate.classical.core import (NullSpec, N_s_cuisine, N_s_recipe, assert_binary_membership,
                                          frequency, monte_carlo, n_ij, null_cuisine,
                                          sample_without_replacement, size_hist)

PROF = {"a": {1, 2, 3}, "b": {2, 3, 4}, "c": {9}, "d": {1, 9}}


def test_n_ij_and_N_s_by_hand():
    assert n_ij(PROF["a"], PROF["b"]) == 2
    # recipe {a,b,c}: pairs ab=2, ac=0, bc=0 → mean over 3 pairs = 2/3
    assert N_s_recipe(["a", "b", "c"], PROF) == pytest.approx(2 / 3)
    assert N_s_recipe(["a"], PROF) is None                         # undefined for n_R < 2
    # cuisine mean ignores undefined recipes
    assert N_s_cuisine([["a", "b"], ["c", "d"], ["a"]], PROF) == pytest.approx((2 + 1) / 2)


def test_binary_membership_invariant():
    with pytest.raises(ValueError):
        assert_binary_membership([["a", "a", "b"]])


def test_sampler_preserves_size_and_distinctness():
    rng = np.random.default_rng(0)
    sizes = np.array([1, 3, 5, 3, 7] * 50)
    out = sample_without_replacement(sizes, np.ones(10), rng)
    assert [len(x) for x in out] == list(sizes)
    assert all(len(set(x)) == len(x) for x in out)


def test_frequency_weighting_tracks_weights():          # A2 Q3 regression: weighted draw follows weights
    rng = np.random.default_rng(20261006)
    w = np.array([50.0, 20, 10, 5, 5, 4, 3, 2, 1])
    out = sample_without_replacement(np.ones(20000, dtype=int), w, rng)
    counts = np.bincount(np.concatenate(out), minlength=len(w)) / 20000
    assert np.allclose(counts, w / w.sum(), atol=0.01)


def test_null_cuisines_preserve_recipe_sizes():
    recipes = [["a", "b"], ["a", "c", "d"], ["b", "d"]]
    uni = ["a", "b", "c", "d"]
    freq = frequency(recipes)
    cat = {"a": "x", "b": "x", "c": "y", "d": "y"}
    rng = np.random.default_rng(1)
    for kind in ("uniform", "frequency", "category", "category_frequency"):
        nc = null_cuisine(recipes, NullSpec(kind, uni, freq, cat), rng)
        assert size_hist(nc) == size_hist(recipes), kind
        if kind.startswith("category"):
            assert [sorted(cat[i] for i in r) for r in nc] == [sorted(cat[i] for i in r) for r in recipes]


def test_monte_carlo_documents_itself_and_detects_signal():
    # a cuisine that deliberately pairs ingredients sharing compounds
    prof = {f"i{k}": ({k, k + 1} if k % 2 == 0 else {k - 1, k}) for k in range(20)}
    recipes = [[f"i{k}", f"i{k + 1}"] for k in range(0, 20, 2)] * 5
    res = monte_carlo(recipes, prof, NullSpec("uniform", list(prof)), M=200, seed=7)
    assert res.real > res.null_mean and res.z > 3 and res.p_emp_upper < 0.01
    for k in ("M", "seed", "size_rule", "universe_size", "weights", "duplicate_policy"):
        assert k in res.record                                       # §82: no undocumented generator
