r"""
DEL-3 gold format (DEL3-GOLD-v0) → engine events.

A gold file is YAML written by ONE annotator for ONE recipe (guideline:
docs/annotation/del3_guideline_v0.md). Loading compiles it into engine Events and
replays them, so any structural mistake (unknown lot, reused lot, over-allocation,
observation without a lot) is rejected with the step it came from.

    g = load_gold("gold/F01.A.yaml")      # -> GoldRecipe; raises GoldError on problems
    g.graph                               # replayed StateGraph
    g.step_of[event_id]                   # instruction step the event came from

Local lot ids ("butter_res") become ENTITY-<recipe>-<local>. Process verbs are
resolved through the B05 vocabulary; an unmapped verb keeps its raw text and gets
process_id None — nothing is guessed.
"""
from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field
from typing import Any, Optional

import yaml

from ..process.vocab import MAPPED, ProcessVocabulary
from .engine import StateError, StateGraph
from .model import (Amount, Belief, Event, NewLot, Op, Provenance, Quantity, Trajectory)

FORMAT = "DEL3-GOLD-v0"
_VOCAB: Optional[ProcessVocabulary] = None


def vocab() -> ProcessVocabulary:
    global _VOCAB
    if _VOCAB is None:
        _VOCAB = ProcessVocabulary.load()
    return _VOCAB


class GoldError(ValueError):
    pass


@dataclass
class GoldRecipe:
    recipe_id: str
    annotator: str
    meta: dict
    events: list[Event]
    step_of: dict[str, int]
    graph: StateGraph = field(repr=False, default=None)


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", str(s)).strip("-")


def _amount(d: Any, where: str) -> Amount:
    if not isinstance(d, dict) or "raw" not in d:
        raise GoldError(f"{where}: qty needs at least 'raw'")
    return Amount(raw=str(d["raw"]), unit=d.get("unit"), value=d.get("value"),
                  lo=d.get("lo"), hi=d.get("hi"))


def load_gold(path: str | pathlib.Path) -> GoldRecipe:
    path = pathlib.Path(path)
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    return compile_gold(doc, where=path.name)


def compile_gold(doc: dict, where: str = "<gold>") -> GoldRecipe:
    if not isinstance(doc, dict) or doc.get("gold_format") != FORMAT:
        raise GoldError(f"{where}: gold_format must be {FORMAT}")
    for k in ("recipe_id", "annotator", "steps"):
        if k not in doc:
            raise GoldError(f"{where}: missing '{k}'")
    rid, who = _slug(doc["recipe_id"]), _slug(doc["annotator"])
    ent = lambda local: f"ENTITY-{rid}-{_slug(local)}"   # noqa: E731
    events: list[Event] = []
    step_of: dict[str, int] = {}
    counter = [0]

    def nid():
        counter[0] += 1
        return f"EVT-{rid}-{who}-{counter[0]:03d}", counter[0]

    def lots(items, w):
        out = []
        for it in items or []:
            if "id" not in it:
                raise GoldError(f"{w}: every lot needs an 'id'")
            concept = it.get("concept")
            if concept is not None and not str(concept).startswith("ING-"):
                concept = f"ING-{_slug(concept).lower()}"
            out.append(NewLot(entity_id=ent(it["id"]), concept_id=concept,
                              label=str(it.get("label", it["id"])),
                              quantity=Quantity.of(_amount(it["qty"], w)) if it.get("qty") else None,
                              fraction=it.get("fraction")))
        return tuple(out)

    def process(raw):
        if raw is None:
            return None, None
        r = vocab().resolve(str(raw))
        return (r.proc_id if r.status == MAPPED else None), str(raw)

    def belief(fieldname, spec, traj, eid):
        if isinstance(spec, dict):
            return Belief(fieldname, spec.get("value"), traj, Provenance.EXPLICIT_SOURCE, eid,
                          unit=spec.get("unit"), lo=spec.get("lo"), hi=spec.get("hi"))
        return Belief(fieldname, spec, traj, Provenance.EXPLICIT_SOURCE, eid)

    def build(e: dict, step: int, w: str, register: bool = True) -> list[Event]:
        if "op" not in e:
            raise GoldError(f"{w}: event without 'op'")
        try:
            op = Op(str(e["op"]).upper())
        except ValueError:
            raise GoldError(f"{w}: unknown op {e['op']!r}") from None
        inputs = tuple(ent(i) for i in (e.get("inputs") or ([e["input"]] if "input" in e else [])))
        pid, praw = process(e.get("process"))
        out: list[Event] = []
        eid, order = nid()
        if op == Op.OMITTED_STEP_CANDIDATE:
            prop = e.get("proposes")
            if not isinstance(prop, dict):
                raise GoldError(f"{w}: candidate needs 'proposes'")
            inner = build(prop, step, w + " (proposed)", register=False)
            if len(inner) != 1:
                raise GoldError(f"{w}: a candidate proposes exactly one event (no plan fields)")
            out.append(Event(eid, order, op, candidate_id=f"CAND-{rid}-{_slug(e['id'])}",
                             proposed=inner[0], rationale=str(e.get("rationale", "")),
                             source_span=e.get("span")))
        elif op in (Op.ACCEPT_CANDIDATE, Op.REJECT_CANDIDATE):
            out.append(Event(eid, order, op, candidate_id=f"CAND-{rid}-{_slug(e['id'])}"))
        elif op in (Op.OBSERVE, Op.SET_FIELD):
            fields = e.get("observe" if op == Op.OBSERVE else "plan") or {}
            if len(fields) != 1 or len(inputs) != 1:
                raise GoldError(f"{w}: {op.value} takes one input and exactly one field")
            (fname, spec), = fields.items()
            traj = Trajectory.OBSERVED_SESSION if op == Op.OBSERVE else Trajectory.PLANNED
            out.append(Event(eid, order, op, inputs=inputs, belief=belief(fname, spec, traj, eid),
                             source_span=e.get("span")))
        else:
            out.append(Event(eid, order, op, inputs=inputs, outputs=lots(e.get("outputs"), w),
                             process_id=pid, process_raw=praw, location=e.get("location"),
                             source_span=e.get("span")))
            # planned endpoints/states become one SET_FIELD each, on the event's result lot
            target = (out[0].outputs[0].entity_id if (out[0].outputs and op != Op.CREATE)
                      else (inputs[0] if inputs else None))
            for fname, spec in (e.get("plan") or {}).items():
                if target is None:
                    raise GoldError(f"{w}: 'plan' needs an input or output lot")
                pe, po = nid()
                out.append(Event(pe, po, Op.SET_FIELD, inputs=(target,),
                                 belief=belief(fname, spec, Trajectory.PLANNED, pe)))
        if register:
            for ev in out:
                step_of[ev.event_id] = step
        return out

    for s in doc["steps"]:
        step = int(s.get("step", 0))
        for k, e in enumerate(s.get("events") or [], 1):
            events.extend(build(e, step, f"step {step} event {k}"))

    g = StateGraph()
    for ev in events:                     # apply one by one to report the failing step
        try:
            g.apply(ev)
        except StateError as exc:
            raise GoldError(f"{where}: step {step_of.get(ev.event_id, '?')} "
                            f"({ev.op.value}): {exc}") from None
    meta = {k: v for k, v in doc.items() if k != "steps"}
    return GoldRecipe(rid, who, meta, events, step_of, g)
