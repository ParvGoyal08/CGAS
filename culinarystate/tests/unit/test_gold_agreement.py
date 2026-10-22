r"""P4 tests — DEL-3 gold loader (YAML → engine events) and ID-invariant agreement."""
from __future__ import annotations

import pathlib
import unittest

from culinarystate.state_graph.agreement import agreement, signatures
from culinarystate.state_graph.gold import GoldError, compile_gold, load_gold

GOLD = pathlib.Path(__file__).resolve().parents[2] / "gold" / "fixtures"


def doc(steps):
    return {"gold_format": "DEL3-GOLD-v0", "recipe_id": "T", "annotator": "X", "steps": steps}


class Loader(unittest.TestCase):

    def test_gold_compiles_and_replays(self):
        a = load_gold(GOLD / "F01.A.yaml")
        rest = a.graph.entity("ENTITY-FIX-F01-butter_rest".replace("_", "-"))
        self.assertEqual(rest.quantity.render(), "50 g − 1 tbsp")      # symbolic, no grams invented
        self.assertIsNone(rest.quantity.resolved())
        self.assertEqual(a.graph.entity("ENTITY-FIX-F01-butter-res").status, "CONSUMED")
        self.assertEqual(a.graph.active(), ["ENTITY-FIX-F01-dish"])

    def test_process_verbs_resolved_and_unknown_kept_raw(self):
        g = compile_gold(doc([{"step": 1, "events": [
            {"op": "CREATE", "outputs": [{"id": "carrot", "concept": "carrot"}]},
            {"op": "TRANSFORM", "input": "carrot", "process": "Julienne"},
            {"op": "TRANSFORM", "input": "carrot", "process": "Stirring"}]}]))
        tr = [e for e in g.events if e.op.value == "TRANSFORM"]
        self.assertEqual((tr[0].process_id, tr[0].process_raw), (None, "Julienne"))
        self.assertEqual(tr[1].process_id, "PROC-stir")

    def test_structural_errors_name_the_step(self):
        with self.assertRaisesRegex(GoldError, "step 2"):
            compile_gold(doc([
                {"step": 1, "events": [{"op": "CREATE", "outputs": [
                    {"id": "a", "concept": "a"}, {"id": "b", "concept": "b"}]},
                    {"op": "MERGE", "inputs": ["a", "b"], "outputs": [{"id": "ab"}]}]},
                {"step": 2, "events": [{"op": "TRANSFORM", "input": "a"}]}]))   # a was consumed
        with self.assertRaises(GoldError):
            compile_gold({"gold_format": "WRONG", "recipe_id": "T", "annotator": "X", "steps": []})

    def test_plan_fields_become_planned_beliefs(self):
        a = load_gold(GOLD / "F01.A.yaml")
        gb = a.graph.entity("ENTITY-FIX-F01-garlic-butter")
        self.assertEqual(gb.fields["aroma_endpoint"].value, "fragrant")
        self.assertEqual(gb.fields["aroma_endpoint"].trajectory.value, "PLANNED")


class Agreement(unittest.TestCase):
    A, B, C = (load_gold(GOLD / f"F01.{x}.yaml") for x in "ABC")

    def test_same_meaning_different_names_is_perfect(self):
        r = agreement(self.A, self.B)
        for k in ("event_f1", "edge_f1", "merge_split_f1"):
            self.assertEqual(r[k]["f1"], 1.0, k)
        for k in ("quantity_agreement", "allocation_agreement", "field_agreement"):
            self.assertEqual(r[k], 1.0, k)

    def test_missed_reserve_is_detected_and_explained(self):
        r = agreement(self.A, self.C)
        self.assertLess(r["merge_split_f1"]["f1"], 0.5)
        self.assertIn("RESERVED_AS: [butter] -> [RESERVE:reserve(butter).reserved]",
                      r["merge_split_f1"]["a_only"])
        self.assertEqual(r["quantity_agreement"], 1.0)        # stated amounts still agree

    def test_signatures_are_annotator_independent(self):
        sa, sb = signatures(self.A), signatures(self.B)
        self.assertEqual(sorted(sa.values()), sorted(sb.values()))

    def test_symmetric(self):
        ab, ba = agreement(self.A, self.C), agreement(self.C, self.A)
        self.assertEqual(ab["edge_f1"]["f1"], ba["edge_f1"]["f1"])
        self.assertEqual(ab["merge_split_f1"]["f1"], ba["merge_split_f1"]["f1"])


if __name__ == "__main__":
    unittest.main()
