r"""
WP-07 tests — DEL-3 state engine.

Run from the repo root (stdlib only; pytest also collects these):
    PYTHONPATH=src python -m unittest discover -s tests -t . -v

Three layers:
  1. hand-written expectations for each of the 10 fixture recipes
     (what a careful human would say the state is — not engine output echoed back);
  2. determinism: replay twice, JSON round-trip, incremental log vs batch replay;
  3. rule enforcement + seeded randomised invariants (stands in for hypothesis,
     which is not installed; port to hypothesis when the CI environment exists).
"""
from __future__ import annotations

import json
import random
import unittest

from culinarystate.state_graph import (Amount, Belief, EventLog, Op, Provenance,
                                       StateError, Trajectory, replay)
from culinarystate.state_graph.io import event_from_dict, event_to_dict
from tests.fixtures.del3_fixtures import (FIXTURES, E, Q, A, lot, observed, planned,
                                          predicted)


def q(graph, eid):
    ent = graph.entity(eid)
    return ent.quantity.to_dict() if ent.quantity else None


# ===================================================================== layer 1
class FixtureExpectations(unittest.TestCase):

    def test_F01_reserve_is_symbolic_and_observation_overrides(self):
        g = replay(FIXTURES["F01"][1]())
        # three identities: concept vs lot vs version
        b = g.entity("ENTITY-F01-butter")
        self.assertEqual(b.concept_id, "ING-butter")
        self.assertEqual([v[0] for v in b.versions],
                         ["STATE-ENTITY-F01-butter-v1", "STATE-ENTITY-F01-butter-v2"])
        self.assertEqual(b.status, "CONSUMED")
        # reserved portion: stated as 1 tbsp, never converted to grams
        res = q(g, "ENTITY-F01-butter-res")
        self.assertEqual(res["expr"], "1 tbsp")
        self.assertEqual(res["resolved"]["unit"], "tbsp")
        # the rest is "50 g − 1 tbsp": unresolved, no invented grams (v4.0 AN2)
        rest = q(g, "ENTITY-F01-butter-rest")
        self.assertEqual(rest["expr"], "50 g − 1 tbsp")
        self.assertIsNone(rest["resolved"])
        self.assertEqual(rest["units"], ["g", "tbsp"])
        # inherited belief: the reserved portion was melted when set aside
        resv = g.entity("ENTITY-F01-butter-res")
        self.assertEqual(resv.fields["phase"].value, "solid")             # observation wins
        self.assertEqual(resv.fields["phase"].trajectory, Trajectory.OBSERVED_SESSION)
        reason, old = resv.audit["phase"][0]
        self.assertEqual((reason, old.value, old.trajectory),
                         ("OVERRIDDEN_BY_OBSERVATION", "melted", Trajectory.PLANNED))
        # recombination consumes the reserved lot; the dish is the only live lot
        self.assertEqual(resv.status, "CONSUMED")
        self.assertEqual(g.active(), ["ENTITY-F01-dish"])
        self.assertEqual(g.entity("ENTITY-F01-dish").parents,
                         ("ENTITY-F01-garlic-butter", "ENTITY-F01-pasta", "ENTITY-F01-butter-res"))
        self.assertIsNone(g.entity("ENTITY-F01-garlic-butter").concept_id)  # intermediate
        rels = {e[0] for e in g.edges}
        self.assertTrue({"TRANSFORMS_INTO", "RESERVED_AS", "SPLITS_INTO", "MERGES_INTO",
                         "OBSERVED_AS", "RECOMBINED_WITH"} <= rels)

    def test_F02_equal_fractions_resolve_exactly(self):
        g = replay(FIXTURES["F02"][1]())
        parts = [q(g, f"ENTITY-F02-piece{k}")["resolved"] for k in range(1, 5)]
        self.assertTrue(all(p["value"] == 125 and p["unit"] == "g" for p in parts))
        self.assertEqual(sum(p["value"] for p in parts), 500)              # conservation
        self.assertEqual(g.entity("ENTITY-F02-dough").status, "CONSUMED")

    def test_F03_unknown_stays_unknown_and_discard_is_recorded(self):
        g = replay(FIXTURES["F03"][1]())
        pot = q(g, "ENTITY-F03-pot")
        self.assertEqual(pot["expr"], "300 g + 2 L")                       # g and L never added
        self.assertIsNone(pot["resolved"])
        # draining into two unspecified parts: both quantities UNKNOWN, not guessed
        self.assertIsNone(g.entity("ENTITY-F03-cooked-pasta").quantity)
        self.assertIsNone(g.entity("ENTITY-F03-cooking-water").quantity)
        self.assertEqual(q(g, "ENTITY-F03-water-res")["expr"], "100 ml")
        self.assertIsNone(g.entity("ENTITY-F03-water-rest").quantity)       # parent unknown
        self.assertEqual(g.entity("ENTITY-F03-water-rest").status, "DISCARDED")
        self.assertIn(("DISCARDED_FROM", ("ENTITY-F03-water-rest",), (), "EVT-F03-05"), g.edges)

    def test_F04_observation_outranks_plan_and_later_prediction(self):
        g = replay(FIXTURES["F04"][1]())
        on = g.entity("ENTITY-F04-onion")
        cur = on.fields["colour_endpoint"]
        self.assertEqual((cur.value, cur.trajectory), ("pale", Trajectory.OBSERVED_SESSION))
        reasons = [(r, b.value, b.trajectory) for r, b in on.audit["colour_endpoint"]]
        self.assertEqual(reasons, [
            ("OVERRIDDEN_BY_OBSERVATION", "golden", Trajectory.PLANNED),
            ("SHADOWED_BY_OBSERVATION", "golden", Trajectory.PREDICTED)])
        # "medium heat" is a qualitative label, never a temperature
        heat = on.fields["heat_level"]
        self.assertEqual((heat.value, heat.unit, heat.lo, heat.hi), ("medium", None, None, None))
        self.assertNotIn("temperature", on.fields)
        self.assertEqual(len(on.versions), 3)                              # create, slice, cook

    def test_F05_fraction_of_symbolic_quantity_and_location(self):
        g = replay(FIXTURES["F05"][1]())
        fz = q(g, "ENTITY-F05-sauce-freeze")
        self.assertEqual(fz["expr"], "0.5 × (400 g) + 0.5 × (1 onion)")
        self.assertIsNone(fz["resolved"])
        self.assertEqual(fz["units"], ["g", "onion"])
        rest = q(g, "ENTITY-F05-sauce-rest")
        self.assertEqual(rest["expr"], "0.5 × (400 g) + 0.5 × (1 onion)")
        self.assertEqual(g.entity("ENTITY-F05-sauce-freeze").location, "freezer")
        # the planned simmer duration is inherited by both halves
        self.assertEqual(g.entity("ENTITY-F05-sauce-rest").fields["duration"].unit, "min")

    def test_F06_parts_of_a_whole_have_no_invented_mass(self):
        g = replay(FIXTURES["F06"][1]())
        self.assertIsNone(g.entity("ENTITY-F06-yolks").quantity)
        self.assertIsNone(g.entity("ENTITY-F06-whites").quantity)
        self.assertEqual(g.entity("ENTITY-F06-whites").fields["texture_endpoint"].value, "stiff peaks")
        self.assertEqual(g.entity("ENTITY-F06-yolks").concept_id, "ING-egg-yolk")

    def test_F07_verbal_quantity_stays_qualitative(self):
        g = replay(FIXTURES["F07"][1]())
        salt = g.entity("ENTITY-F07-salt").quantity.terms[0].amount
        self.assertEqual((salt.raw, salt.value, salt.lo, salt.hi), ("a pinch", None, None, None))
        self.assertIsNone(q(g, "ENTITY-F07-marinade")["resolved"])
        self.assertEqual(g.entity("ENTITY-F07-marinating").location, "fridge")
        self.assertEqual(g.active(), ["ENTITY-F07-marinating"])

    def test_F08_accepted_candidate_is_applied_once(self):
        events = FIXTURES["F08"][1]()
        before = replay(events[:2])
        self.assertNotIn("hydration", before.entity("ENTITY-F08-chickpeas").fields)
        self.assertEqual(before.candidates["CAND-F08-1"]["status"], "PROPOSED")
        g = replay(events)
        c = g.candidates["CAND-F08-1"]
        self.assertEqual((c["status"], c["decided_by"]), ("ACCEPTED", "EVT-F08-03"))
        cp = g.entity("ENTITY-F08-chickpeas")
        self.assertEqual(cp.fields["hydration"].value, "soaked")
        self.assertEqual(len(cp.versions), 2)

    def test_F09_rejected_candidate_changes_nothing(self):
        g = replay(FIXTURES["F09"][1]())
        self.assertEqual(g.candidates["CAND-F09-1"]["status"], "REJECTED")
        procs = [v[3] for v in g.entity("ENTITY-F09-dough").versions]
        self.assertEqual(procs, [None, "shape", "bake"])                   # no "proof" version

    def test_F10_interval_fraction_keeps_correlation(self):
        g = replay(FIXTURES["F10"][1]())
        use = q(g, "ENTITY-F10-oil-use")["resolved"]
        rest = q(g, "ENTITY-F10-oil-rest")["resolved"]
        self.assertEqual((use["lo"], use["hi"], use["unit"]), (1.0, 1.5, "tbsp"))
        # (1 − ½) × [2, 3] = [1, 1.5] — NOT [2,3] − [1,1.5] = [0.5, 2] (lost correlation)
        self.assertEqual((rest["lo"], rest["hi"]), (1.0, 1.5))


# ===================================================================== layer 2
class Determinism(unittest.TestCase):

    def test_replay_is_deterministic_for_every_fixture(self):
        for name, (_, build) in FIXTURES.items():
            with self.subTest(fixture=name):
                self.assertEqual(replay(build()).digest(), replay(build()).digest())

    def test_json_round_trip_replays_identically(self):
        for name, (_, build) in FIXTURES.items():
            with self.subTest(fixture=name):
                evs = build()
                blob = json.dumps([event_to_dict(e) for e in evs], sort_keys=True)
                back = [event_from_dict(d) for d in json.loads(blob)]
                self.assertEqual(back, evs)
                self.assertEqual(replay(back).digest(), replay(evs).digest())

    def test_incremental_log_equals_batch_replay(self):
        for name, (_, build) in FIXTURES.items():
            with self.subTest(fixture=name):
                evs = build()
                log = EventLog()
                for e in evs:
                    log.append(e)
                self.assertEqual(log.state.digest(), replay(log.events).digest())
                self.assertEqual(log.events, tuple(evs))


# ===================================================================== layer 3
class RulesEnforced(unittest.TestCase):

    def _base(self):
        return [E("EVT-T-01", 1, Op.CREATE, outputs=(
            lot("ENTITY-T-a", "ING-a", "a", Q(A("100 g", "g", 100))),
            lot("ENTITY-T-b", "ING-b", "b", Q(A("50 g", "g", 50)))))]

    def assertRejected(self, events, bad):
        log = EventLog(events)
        before = log.state.digest()
        with self.assertRaises(StateError):
            log.append(bad)
        self.assertEqual(log.state.digest(), before)      # a rejected event leaves no trace
        self.assertEqual(len(log.events), len(events))

    def test_ids_never_reused(self):
        self.assertRejected(self._base(), E("EVT-T-02", 2, Op.CREATE,
                                            outputs=(lot("ENTITY-T-a", "ING-a", "again"),)))

    def test_identity_prefixes_enforced(self):
        self.assertRejected(self._base(), E("EVT-T-02", 2, Op.CREATE,
                                            outputs=(lot("butter-1", "ING-a", "x"),)))
        self.assertRejected(self._base(), E("EVT-T-02", 2, Op.CREATE,
                                            outputs=(lot("ENTITY-T-c", "butter", "x"),)))

    def test_consumed_lot_cannot_be_reused(self):
        evs = self._base() + [E("EVT-T-02", 2, Op.MERGE, inputs=("ENTITY-T-a", "ENTITY-T-b"),
                                outputs=(lot("ENTITY-T-ab", None, "ab"),))]
        self.assertRejected(evs, E("EVT-T-03", 3, Op.TRANSFORM, inputs=("ENTITY-T-a",)))

    def test_order_and_event_ids(self):
        evs = self._base()
        self.assertRejected(evs, E("EVT-T-02", 1, Op.TRANSFORM, inputs=("ENTITY-T-a",)))
        self.assertRejected(evs, E("EVT-T-01", 5, Op.TRANSFORM, inputs=("ENTITY-T-a",)))

    def test_fractions_and_overallocation(self):
        evs = self._base()
        self.assertRejected(evs, E("EVT-T-02", 2, Op.SPLIT, inputs=("ENTITY-T-a",), outputs=(
            lot("ENTITY-T-x", None, "x", fraction=0.6), lot("ENTITY-T-y", None, "y", fraction=0.6))))
        self.assertRejected(evs, E("EVT-T-02", 2, Op.SPLIT, inputs=("ENTITY-T-a",), outputs=(
            lot("ENTITY-T-x", None, "x", Q(A("80 g", "g", 80))),
            lot("ENTITY-T-y", None, "y", Q(A("40 g", "g", 40))))))

    def test_observation_and_provenance_rules(self):
        evs = self._base()
        self.assertRejected(evs, E("EVT-T-02", 2, Op.OBSERVE, inputs=("ENTITY-T-a",),
                                   belief=planned("phase", "x", "EVT-T-02")))
        self.assertRejected(evs, E("EVT-T-02", 2, Op.SET_FIELD, inputs=("ENTITY-T-a",),
                                   belief=observed("phase", "x", "EVT-T-02")))
        # law B3: a model estimate can never be recorded as a plan or an observation
        bad = Belief("phase", "x", Trajectory.PLANNED, Provenance.MODEL_ESTIMATED, "EVT-T-02")
        self.assertRejected(evs, E("EVT-T-02", 2, Op.SET_FIELD, inputs=("ENTITY-T-a",), belief=bad))

    def test_reserve_recombine_discipline(self):
        evs = self._base()
        self.assertRejected(evs, E("EVT-T-02", 2, Op.RECOMBINE, inputs=("ENTITY-T-a", "ENTITY-T-b"),
                                   outputs=(lot("ENTITY-T-ab", None, "ab"),)))
        evs2 = evs + [E("EVT-T-02", 2, Op.RESERVE, inputs=("ENTITY-T-a",), outputs=(
            lot("ENTITY-T-ar", None, "res", Q(A("10 g", "g", 10))), lot("ENTITY-T-arest", None, "rest")))]
        self.assertRejected(evs2, E("EVT-T-03", 3, Op.MERGE, inputs=("ENTITY-T-ar", "ENTITY-T-b"),
                                    outputs=(lot("ENTITY-T-m", None, "m"),)))
        g = replay(evs2)
        self.assertEqual(q(g, "ENTITY-T-arest")["resolved"]["value"], 90)   # same unit → exact

    def test_unknown_candidate_cannot_be_decided(self):
        self.assertRejected(self._base(), E("EVT-T-02", 2, Op.ACCEPT_CANDIDATE, candidate_id="CAND-X"))

    def test_event_failing_halfway_leaves_no_partial_state(self):
        # the first new lot is valid, the second reuses an ID: nothing may be created
        self.assertRejected(self._base(), E("EVT-T-02", 2, Op.CREATE, outputs=(
            lot("ENTITY-T-new", "ING-n", "new"), lot("ENTITY-T-a", "ING-a", "dup"))))
        # the first input is discardable, the second already consumed: nothing discarded
        evs = self._base() + [E("EVT-T-02", 2, Op.RESERVE, inputs=("ENTITY-T-b",), outputs=(
            lot("ENTITY-T-br", None, "res", Q(A("5 g", "g", 5))), lot("ENTITY-T-brest", None, "rest")))]
        self.assertRejected(evs, E("EVT-T-03", 3, Op.DISCARD, inputs=("ENTITY-T-a", "ENTITY-T-b")))
        log = EventLog(evs)
        try:
            log.append(E("EVT-T-03", 3, Op.DISCARD, inputs=("ENTITY-T-a", "ENTITY-T-b")))
        except StateError:
            pass
        self.assertEqual(log.state.entity("ENTITY-T-a").status, "ACTIVE")
        self.assertNotIn("ENTITY-T-new", replay(self._base()).entities)


class RandomisedInvariants(unittest.TestCase):
    """Seeded random event sequences; every sequence must satisfy the invariants."""

    UNITS = ["g", "ml", "tbsp", "egg", None]

    def _sequence(self, rng: random.Random):
        evs, order, n = [], 0, 0

        def nxt():
            nonlocal order
            order += 1
            return order

        created_units = set()
        lots = []
        for _ in range(rng.randint(2, 5)):
            n += 1
            u = rng.choice(self.UNITS)
            val = rng.choice([None, float(rng.randint(1, 500))])
            amt = None if u is None else Amount(raw=f"{val} {u}" if val else f"some {u}", unit=u, value=val)
            created_units.add(u)
            lots.append(lot(f"ENTITY-R-{n}", f"ING-r{n}", f"lot{n}", Q(amt) if amt else None))
        evs.append(E(f"EVT-R-{nxt()}", order, Op.CREATE, outputs=tuple(lots)))
        log = EventLog(evs)
        for _ in range(rng.randint(5, 25)):
            act = [k for k, v in log.state.entities.items() if v.status == "ACTIVE"]
            if not act:
                break
            choice = rng.choice(["T", "M", "S", "R", "D", "X", "O", "P"])
            i = rng.choice(act)
            oid = f"EVT-R-{order + 1}"
            if choice == "T":
                e = E(oid, order + 1, Op.TRANSFORM, inputs=(i,), process_raw=rng.choice(["chop", "heat"]))
            elif choice == "M" and len(act) >= 2:
                a, b = rng.sample(act, 2)
                n += 1
                e = E(oid, order + 1, Op.MERGE, inputs=(a, b), outputs=(lot(f"ENTITY-R-{n}", None, "m"),))
            elif choice in ("S", "R"):
                k = 2 if choice == "R" else rng.randint(2, 4)
                fr = rng.choice([None, 1.0 / k])
                outs = []
                for j in range(k):
                    n += 1
                    last = j == k - 1
                    outs.append(lot(f"ENTITY-R-{n}", None, "part",
                                    fraction=None if (fr is None or last) else fr))
                e = E(oid, order + 1, Op.RESERVE if choice == "R" else Op.SPLIT, inputs=(i,),
                      outputs=tuple(outs))
            elif choice == "D":
                e = E(oid, order + 1, Op.DISCARD, inputs=(i,))
            elif choice == "X":
                e = E(oid, order + 1, Op.TRANSFER, inputs=(i,), location=rng.choice(["bowl", "pan"]))
            elif choice == "O":
                e = E(oid, order + 1, Op.OBSERVE, inputs=(i,), belief=observed("phase", "x", oid))
            else:
                e = E(oid, order + 1, Op.SET_FIELD, inputs=(i,), belief=predicted("phase", "y", oid))
            try:
                log.append(e)
                order += 1
            except StateError:
                pass  # an invalid random event must leave the log unchanged
        return list(log.events), created_units

    def test_invariants_hold_on_200_random_sessions(self):
        rng = random.Random(20261007)
        for trial in range(200):
            evs, created_units = self._sequence(rng)
            with self.subTest(trial=trial):
                g1, g2 = replay(evs), replay(evs)
                self.assertEqual(g1.digest(), g2.digest())                  # determinism
                back = [event_from_dict(d) for d in json.loads(json.dumps(
                    [event_to_dict(e) for e in evs]))]
                self.assertEqual(replay(back).digest(), g1.digest())        # round trip
                for ent in g1.entities.values():
                    if ent.quantity is not None:                            # no invented units
                        self.assertTrue(ent.quantity.units() <= created_units,
                                        f"{ent.entity_id} units {ent.quantity.units()}")
                    nums = [int(v[0].rsplit("-v", 1)[1]) for v in ent.versions]
                    self.assertEqual(nums, list(range(1, len(nums) + 1)))  # monotone versions
                consumed_inputs = {}
                for e in evs:                                               # append-only use
                    for i in e.inputs:
                        self.assertNotIn(i, consumed_inputs, f"{i} reused after {consumed_inputs.get(i)}")
                    if e.op in (Op.MERGE, Op.SPLIT, Op.RESERVE, Op.RECOMBINE):
                        for i in e.inputs:
                            consumed_inputs[i] = e.event_id
                    if e.op == Op.DISCARD:
                        for i in e.inputs:
                            consumed_inputs[i] = e.event_id
                # conservation where decidable: same-unit fraction splits sum to the parent
                for e in evs:
                    if e.op == Op.SPLIT and all(o.fraction is not None for o in e.outputs[:-1]):
                        parent = g1.entity(e.inputs[0]).quantity
                        pr = parent.resolved() if parent else None
                        kids = [g1.entity(o.entity_id).quantity for o in e.outputs]
                        if pr is not None and pr.value is not None and all(k is not None for k in kids):
                            total = sum(k.resolved().value for k in kids)
                            self.assertAlmostEqual(total, pr.value, places=9)


if __name__ == "__main__":
    unittest.main()
