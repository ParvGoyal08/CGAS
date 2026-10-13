import pandas as pd

from tools.data_report import PLUGINS, Plugin, profile


def _plugin(df, **kw):
    return Plugin("t", ["tests/unit/test_data_report.py"], lambda _: df, **kw)


def test_duplicates_missingness_and_long_tail():
    df = pd.DataFrame({"id": ["a", "b", "b", "c"], "src": ["s1", "s1", "s1", "s2"],
                       "status": ["UNKNOWN", "", "MEASURED", "MEASURED"], "food": ["x", "x", "x", "y"]})
    r = profile(_plugin(df, key="id", freq="food", roles={"source": "src"}))
    assert r["key_duplicates"] == 1 and r["exact_duplicate_rows"] == 0
    assert r["missingness"]["status"] == {"empty": 0.25, "unknown": 0.25}       # UNKNOWN counted apart from empty
    assert r["long_tail"]["distinct"] == 2 and r["distributions"]["source"]["s1"] == 3


def test_missing_inputs_report_not_available():
    p = Plugin("ghost", ["does/not/exist.csv"], lambda _: None)
    assert profile(p)["available"] is False


def test_every_registered_plugin_runs():
    for name, p in PLUGINS.items():
        r = profile(p)
        assert "available" in r, name
