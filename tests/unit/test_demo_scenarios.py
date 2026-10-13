r"""P11: every demo scenario runs on the real components; its decision mode is the intended one,
and every cited id exists (template verbaliser — no network)."""
from culinarystate.demo.scenarios import cited_ok, run_all

EXPECTED = {"S01": "ANSWER", "S02": "ANSWER", "S03": "ASK", "S04": "DIAGNOSE", "S05": "RECOVER",
            "S06": "ANSWER", "S07": "ANSWER", "S08": "ABSTAIN", "S09": "ANSWER", "S10": "BLOCKED", "S11": "RECOVER"}


def test_all_scenarios():
    rs = {r["id"]: r for r in run_all()}
    assert {k: v["mode"] for k, v in rs.items()} == EXPECTED
    assert rs["S06"]["evidence_class"] == "observed" and rs["S07"]["evidence_class"] == "near"
    assert "1 tbsp" in rs["S01"]["answer"] and "50 g − 1 tbsp" in rs["S01"]["answer"]
    assert "status='UNKNOWN'" in rs["S09"]["detail"]["grams"]                  # volume → grams never invented
    assert rs["S04"]["answer"]["statement"] is None                          # unverified ≠ finding
    assert all(cited_ok(r) for r in rs.values())
    assert rs["S05"]["detail"]["reserved_lot"] is not None


def test_streamlit_app_renders_every_scenario():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(__import__("pathlib").Path(__file__).resolve().parents[2] / "app/demo.py"), default_timeout=60).run()
    assert not at.exception
    for label in at.sidebar.radio[1].options:
        at.sidebar.radio[1].set_value(label).run()
        assert not at.exception, label
