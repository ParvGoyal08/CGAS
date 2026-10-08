r"""P2 tests — process ontology v0 ledgers and the resolver (stdlib unittest)."""
from __future__ import annotations

import csv
import unittest

from culinarystate.process import ProcessVocabulary
from culinarystate.process.vocab import LEDGER
from culinarystate.state_graph import Op

V = ProcessVocabulary.load()


def rows(name):
    with (LEDGER / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class LedgerIntegrity(unittest.TestCase):
    """Re-checked from the CSVs, independently of the build script."""

    def test_ids_families_parents(self):
        fams = {r["family_id"] for r in rows("process_families_v0.csv")}
        procs = {r["proc_id"]: r for r in rows("proc_v0.csv")}
        for pid, r in procs.items():
            self.assertRegex(pid, r"^PROC-[a-z0-9]+(-[a-z0-9]+)*$")
            self.assertIn(r["family_id"], fams)
            if r["parent_id"]:
                self.assertIn(r["parent_id"], procs)
            self.assertEqual(r["status"], "PROPOSED")

    def test_no_scientific_values_were_invented(self):
        for r in rows("proc_v0.csv"):
            self.assertEqual((r["parameters"], r["mechanism_links"]), ("UNKNOWN", "UNKNOWN"))
            self.assertTrue(r["xref_foodon"] == "UNRESOLVED_EXTERNAL" or "[V RS-05-01]" in r["xref_foodon"])

    def test_engine_op_hints_are_real_engine_operations(self):
        for r in rows("proc_v0.csv"):
            self.assertIn(r["engine_op_hint"], Op.__members__)

    def test_every_recipedb_term_is_classified_exactly_once(self):
        tm = rows("recipedb_term_map_v0.csv")
        terms = [r["recipedb_term"] for r in tm]
        self.assertEqual(len(terms), 270)
        self.assertEqual(len(set(terms)), 270)
        self.assertTrue(all(V.resolve(t).status != "UNMAPPED" for t in terms))


class Resolver(unittest.TestCase):

    def test_inflection_synonym_and_accent(self):
        self.assertEqual(V.resolve("Stirring").proc_id, "PROC-stir")
        self.assertEqual(V.resolve("put").proc_id, "PROC-place")
        self.assertEqual(V.resolve("sauté").proc_id, "PROC-saute")
        self.assertEqual(V.resolve("Pre-heat").proc_id, "PROC-preheat")

    def test_regional_synonyms(self):
        for word in ("tadka", "chhaunk", "baghar"):
            self.assertEqual(V.resolve(word).proc_id, "PROC-temper-spices", word)
        self.assertEqual(V.resolve("bhunao").proc_id, "PROC-bhuno")

    def test_ambiguous_returns_candidates_not_a_guess(self):
        r = V.resolve("reduce")
        self.assertEqual(r.status, "AMBIGUOUS")
        self.assertIsNone(r.proc_id)
        self.assertEqual(set(r.candidates), {"PROC-reduce-liquid", "PROC-adjust-heat"})
        s = V.resolve("smoking")
        self.assertEqual(s.status, "AMBIGUOUS")
        self.assertIn("PROC-smoke", s.candidates)

    def test_non_process_classes(self):
        self.assertEqual((V.resolve("wok").status, V.resolve("wok").term_class), ("NON_PROCESS", "TOOL"))
        oc = V.resolve("overcook")
        self.assertEqual((oc.status, oc.term_class, oc.proc_id), ("NON_PROCESS", "ENDPOINT_STATE", "PROC-cook"))
        self.assertEqual(V.resolve("dash").term_class, "QUANTITY_TERM")

    def test_unknown_verb_is_unmapped_with_raw_kept(self):
        r = V.resolve("Julienne")
        self.assertEqual((r.status, r.raw, r.proc_id), ("UNMAPPED", "Julienne", None))

    def test_escape_processes_resolve(self):
        for slug in ("sous-vide", "air-fry", "nixtamalize", "dum", "bhuno", "flambe",
                     "confit", "proof", "brine", "cure"):
            self.assertEqual(V.resolve(slug.replace("-", " ")).proc_id, f"PROC-{slug}", slug)


if __name__ == "__main__":
    unittest.main()
