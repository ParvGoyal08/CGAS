import numpy as np

from culinarystate.evolution.csn import compare_all, fit_alternatives, fit_power_law


def _pl_sample(n, a, xmin, seed):
    u = np.random.default_rng(seed).random(n)
    return np.floor((xmin - 0.5) * (1 - u) ** (-1 / (a - 1)) + 0.5).astype(int)


def test_recovers_alpha_on_synthetic_power_law():
    x = _pl_sample(5000, 2.5, 5, 1)
    f = fit_power_law(x)
    assert abs(f.alpha - 2.5) < 0.15 and f.xmin <= 12


def test_exponential_data_not_favouring_power_law():
    x = np.random.default_rng(2).geometric(0.05, 4000)
    f = fit_power_law(x)
    c = compare_all(fit_alternatives(x, f.xmin))
    assert c["power_law_vs_exponential"]["favours"] != "power_law"
