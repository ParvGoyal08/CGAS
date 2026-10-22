r"""P8: study / source-family splits (additive; synthetic data only — no real run before ledger v1 is frozen)."""
import numpy as np
import pandas as pd
import pytest

from culinarystate.transition.del2 import grouped_boot, group_ids, make_folds


def _cells(n_studies=12, per=8, seed=0):
    rng = np.random.default_rng(seed)
    rows = [{"code": f"c{s}-{k}", "study_id": f"STUDY-{s:06d}", "source_family_id": f"FAM-{s // 3}",
             "ingredient": f"i{k % 4}", "proc_sig": "PROC-boil", "y": rng.normal(80, 10)}
            for s in range(n_studies) for k in range(per)]
    return pd.DataFrame(rows)


@pytest.mark.parametrize("split,col", [("study", "study_id"), ("source_family", "source_family_id")])
def test_groups_never_straddle_folds(split, col):
    c = _cells(n_studies=18)                                   # 18 studies → 6 source families ≥ 5 folds
    f = make_folds(c, split, seed=1, cluster={})
    assert c.assign(f=f).groupby(col)["f"].nunique().max() == 1


def test_study_level_bootstrap_and_missing_ids_refused():
    c = _cells()
    g = group_ids(c, "study", {}).to_numpy()
    m, lo, hi = grouped_boot(np.abs(c["y"].to_numpy() - 80), g, n_boot=200, seed=0)
    assert lo <= m <= hi
    with pytest.raises(ValueError):
        make_folds(c.drop(columns="study_id"), "study", 1, {})
    with pytest.raises(ValueError):
        make_folds(_cells(n_studies=3), "study", 1, {})         # fewer groups than folds
