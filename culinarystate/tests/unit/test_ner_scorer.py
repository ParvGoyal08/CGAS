from culinarystate.ner.scorer import Span, leakage_audit, score_spans


def S(s, e, lab, d="d1"):
    return Span(d, s, e, lab)


def test_perfect_and_empty():
    g = [S(0, 5, "ING"), S(10, 14, "PROC")]
    assert score_spans(g, g)["exact"]["micro"]["f1"] == 1.0
    r = score_spans(g, [])
    assert r["exact"]["micro"]["recall"] == 0.0 and r["exact"]["micro"]["fn"] == 2


def test_boundary_error_counts_in_overlap_not_exact():
    g, p = [S(0, 10, "ING")], [S(0, 8, "ING")]
    r = score_spans(g, p)
    assert r["exact"]["micro"]["f1"] == 0.0 and r["overlap"]["micro"]["f1"] == 1.0


def test_label_error_never_matches():
    r = score_spans([S(0, 5, "ING")], [S(0, 5, "PROC")])
    assert r["exact"]["micro"]["tp"] == 0 and r["overlap"]["micro"]["tp"] == 0


def test_overlap_is_one_to_one():
    g = [S(0, 10, "ING")]
    p = [S(0, 4, "ING"), S(5, 10, "ING")]
    r = score_spans(g, p)["overlap"]["micro"]
    assert r["tp"] == 1 and r["fp"] == 1


def test_macro_over_gold_labels():
    g = [S(0, 5, "ING"), S(6, 9, "PROC")]
    p = [S(0, 5, "ING")]
    assert abs(score_spans(g, p)["exact"]["macro_f1"] - 0.5) < 1e-9


def test_leakage_exact_and_near():
    train = {"a": "Boil the potatoes in salted water for 20 minutes then drain well",
             "b": "Whisk eggs and sugar"}
    test = {"x": "boil the potatoes in salted water, for 20 minutes then drain well!",
            "y": "Boil the potatoes in salted water for 20 minutes then drain well and mash",
            "z": "Toast cumin seeds in ghee"}
    r = leakage_audit(train, test, jaccard=0.7)
    assert [e[0] for e in r["exact_duplicates"]] == ["x"]
    assert [n[0] for n in r["near_duplicates"]] == ["y"]
    assert abs(r["leak_rate"] - 2 / 3) < 1e-9


def test_linking_attributes_relations_strata():
    from culinarystate.ner.scorer import attribute_accuracy, frequency_strata, linking_metrics, relation_f1
    lm = linking_metrics({"m1": "ING-onion", "m2": "ING-garlic", "m3": "ING-egg"},
                         {"m1": ["ING-onion"], "m2": ["ING-shallot", "ING-garlic"], "m3": []})
    assert lm["acc_at_1"] == 1 / 3 and lm["recall_at_5"] == 2 / 3 and lm["abstain_rate"] == 1 / 3
    aa = attribute_accuracy({"s1": {"quantity": (2, "UNIT-tbsp"), "form": "Chopped"}, "s2": {"form": "whole"}},
                            {"s1": {"quantity": (2.0, "UNIT-tbsp"), "form": "chopped"}})
    assert aa["quantity"]["accuracy"] == 1.0 and aa["form"]["accuracy"] == 0.5
    rf = relation_f1({("a", "MERGES_INTO", "c"), ("b", "MERGES_INTO", "c")}, {("a", "MERGES_INTO", "c"), ("a", "SPLITS_INTO", "d")})
    assert rf["micro"]["tp"] == 1 and rf["per_relation"]["SPLITS_INTO"]["fp"] == 1
    st = frequency_strata({f"i{k}": 100 - k for k in range(10)})
    assert st["i0"] == "head" and st["i9"] == "tail" and list(st.values()).count("head") == 2
