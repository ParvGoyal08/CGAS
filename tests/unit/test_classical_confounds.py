r"""T24 / B03-lite — frequency and size confounds in food-pairing null comparisons (synthetic data).

Construction: 'popular' ingredients share many compounds with each other; 'rare' ones share few;
recipes are drawn purely by POPULARITY with no pairing preference at all. Then
  * vs the UNIFORM null, the real cuisine looks like it 'prefers shared compounds' (ΔN_s > 0, large z)
    — a pure frequency artefact;
  * vs the FREQUENCY-preserving null, the effect vanishes (|z| small).
  * the frequency-WEIGHTED null removes most but not all of it (weighted sampling without replacement
    under-represents popular–popular pairs);
  * the degree-preserving SWAP null (exact sizes and frequencies) removes it.
This is the confound the frequency controls exist to remove (SSOT §81); the test pins all three."""
import numpy as np

from culinarystate.classical.core import NullSpec, monte_carlo, null_cuisine, sample_without_replacement


def _world(seed=0, n_items=60, n_pop=10, n_rec=400):
    rng = np.random.default_rng(seed)
    items = [f"i{k}" for k in range(n_items)]
    shared = set(range(40))
    profiles = {}
    for k, it in enumerate(items):
        if k < n_pop:
            profiles[it] = shared | {100 + k}                                   # popular: big shared core
        else:
            profiles[it] = {int(x) for x in rng.choice(np.arange(200, 2000), 8, replace=False)}
    w = np.array([20.0 if k < n_pop else 1.0 for k in range(n_items)])
    sizes = rng.integers(3, 9, n_rec)
    recipes = [[items[j] for j in d] for d in sample_without_replacement(sizes, w, rng)]
    freq = {it: sum(it in r for r in recipes) for it in items}
    return items, profiles, recipes, freq


def test_popularity_artefact_across_the_three_nulls():
    items, prof, recipes, freq = _world()
    uni = monte_carlo(recipes, prof, NullSpec("uniform", items), M=30, seed=1)
    fq = monte_carlo(recipes, prof, NullSpec("frequency", items, frequency=freq), M=30, seed=1)
    sw = monte_carlo(recipes, prof, NullSpec("swap", items), M=30, seed=1)
    assert uni.delta > 0 and uni.z > 5                    # pure popularity artefact vs the uniform null
    assert 0 < fq.delta < 0.2 * uni.delta                  # weighted null removes most of it, not all
    assert abs(sw.z) < 3                                   # exact-marginal null removes it


def test_swap_null_preserves_sizes_and_frequencies_exactly():
    items, prof, recipes, freq = _world(seed=6)
    from culinarystate.classical.core import curveball
    nc = curveball(recipes, np.random.default_rng(7))
    assert [len(r) for r in nc] == [len(r) for r in recipes]
    assert {it: sum(it in r for r in nc) for it in items} == freq
    assert nc != [sorted(r) for r in recipes]


def test_nulls_preserve_sizes_and_membership():
    items, prof, recipes, freq = _world(seed=2)
    rng = np.random.default_rng(3)
    for spec in (NullSpec("uniform", items), NullSpec("frequency", items, frequency=freq)):
        nc = null_cuisine(recipes, spec, rng)
        assert [len(r) for r in nc] == [len(r) for r in recipes]
        assert all(len(set(r)) == len(r) for r in nc)


def test_frequency_null_tracks_frequency_ranks():
    items, prof, recipes, freq = _world(seed=4)
    nc = null_cuisine(recipes, NullSpec("frequency", items, frequency=freq), np.random.default_rng(5))
    f_null = {it: sum(it in r for r in nc) for it in items}
    a, b = np.array([freq[i] for i in items]), np.array([f_null[i] for i in items])
    ra, rb = a.argsort().argsort(), b.argsort().argsort()
    assert np.corrcoef(ra, rb)[0, 1] > 0.7
