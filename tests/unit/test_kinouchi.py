r"""T07 invariants only (AC-5), on tiny parameters. No paper-scale run before the pre-registration is frozen."""
import numpy as np
import pytest

from culinarystate.evolution.kinouchi import Config, rank_frequency, simulate

SMALL = dict(T=60, K=5, L=2, M=3, R0=4)


@pytest.mark.parametrize("initial", ["IC-a", "IC-b"])
@pytest.mark.parametrize("stop", ["R_equals_T", "T_steps"])
def test_invariants(initial, stop):
    cfg = Config(**SMALL, initial=initial, stop=stop)
    r = simulate(cfg, seed=1)
    assert len(r.recipes) == (cfg.T if stop == "R_equals_T" else cfg.T + cfg.R0)       # R = T  (A3 both ways)
    assert all(len(x) == cfg.K for x in r.recipes)                                        # K slots
    assert all(len(set(x.tolist())) == cfg.K for x in r.recipes)                          # A6 reject → distinct
    assert r.pool_sizes[-1] == max(cfg.M * len(r.recipes), len(r.founders) if initial == "IC-b" else 0)
    assert ((r.fitness >= 0) & (r.fitness <= 1)).all()


def test_selection_only_accepts_fitter_ingredients():
    cfg = Config(**SMALL)
    r = simulate(cfg, seed=2)
    f = rank_frequency(r)
    assert np.all(np.diff(f) <= 0) and f[0] <= 1.0
    assert np.mean([r.fitness[x].mean() for x in r.recipes[-10:]]) >= np.mean([r.fitness[x].mean() for x in r.recipes[:4]])


def test_deterministic_given_seed():
    a, b = simulate(Config(**SMALL), 7), simulate(Config(**SMALL), 7)
    assert all((x == y).all() for x, y in zip(a.recipes, b.recipes, strict=True))


def test_running_total_fitness_equals_recomputation():
    r = simulate(Config(**SMALL), seed=3)
    f = np.asarray(r.fitness)
    direct = np.mean([f[x].mean() for x in r.recipes])
    assert abs(r.total_fitness[-1] - direct) < 1e-12
