r"""
Event-sourced state engine (DEL-3 core, WP-07).

    graph = replay(events)          # pure: same events → same graph, always
    log = EventLog(); log.append(e) # append-only; validates against current state

State is never stored independently of the log. It is *derived* by replaying
events in order (SSOT §233.3), so a correction is a new event and history is
never rewritten (master prompt law B15).

Rules enforced on every event (raising StateError):
  * orders strictly increase and event IDs are unique;
  * consumed or discarded lots can never be used again (they stay in history);
  * an observation (OBSERVE, trajectory OBSERVED_SESSION) overrides the current
    belief for that field; the overridden belief moves to the audit trail;
  * a later PLANNED/PREDICTED belief never displaces an observed one — it is
    recorded as shadowed in the audit trail instead;
  * split/reserve remainders are symbolic: parent − allocations, no unit
    conversion; a remainder resolves to a number only when every term shares
    one unit;
  * omitted-step candidates change nothing until explicitly accepted.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from typing import Iterable, Optional

from .model import (Amount, Belief, Event, NewLot, Op, Provenance, Quantity, Relation,
                    Term, Trajectory)


class StateError(ValueError):
    """An event is inconsistent with the state it is applied to."""


ACTIVE, CONSUMED, DISCARDED, RESERVED = "ACTIVE", "CONSUMED", "DISCARDED", "RESERVED"
USABLE = {ACTIVE, RESERVED}


@dataclass
class Entity:
    entity_id: str
    concept_id: Optional[str]
    label: str
    status: str
    parents: tuple[str, ...]
    created_by: str
    quantity: Optional[Quantity] = None
    location: Optional[str] = None
    versions: list = field(default_factory=list)       # [(version_id, event_id, op, process)]
    fields: dict = field(default_factory=dict)         # field -> Belief (current)
    audit: dict = field(default_factory=dict)          # field -> [(reason, Belief)]

    def new_version(self, event: Event) -> str:
        vid = f"STATE-{self.entity_id}-v{len(self.versions) + 1}"
        self.versions.append((vid, event.event_id, event.op.value,
                              event.process_id or event.process_raw))
        return vid

    def to_dict(self) -> dict:
        return {
            "concept_id": self.concept_id, "label": self.label, "status": self.status,
            "parents": list(self.parents), "created_by": self.created_by,
            "quantity": self.quantity.to_dict() if self.quantity else None,
            "location": self.location,
            "versions": [list(v) for v in self.versions],
            "fields": {k: b.to_dict() for k, b in sorted(self.fields.items())},
            "audit": {k: [[r, b.to_dict()] for r, b in v] for k, v in sorted(self.audit.items())},
        }


class StateGraph:
    def __init__(self):
        self.entities: dict[str, Entity] = {}
        self.edges: list[tuple[str, tuple[str, ...], tuple[str, ...], str]] = []
        self.candidates: dict[str, dict] = {}
        self.last_order: Optional[int] = None
        self.event_ids: set[str] = set()

    # ------------------------------------------------------------ helpers
    def _usable(self, eid: str, allow=USABLE) -> Entity:
        e = self.entities.get(eid)
        if e is None:
            raise StateError(f"unknown entity {eid}")
        if e.status not in allow:
            raise StateError(f"entity {eid} is {e.status}; cannot be used")
        return e

    def _create(self, lot: NewLot, parents: tuple[str, ...], ev: Event,
                quantity: Optional[Quantity], status: str = ACTIVE) -> Entity:
        if lot.entity_id in self.entities:
            raise StateError(f"entity id {lot.entity_id} reused (IDs are never reused)")
        if not lot.entity_id.startswith("ENTITY-"):
            raise StateError(f"entity ids must start with ENTITY-: {lot.entity_id}")
        if lot.concept_id is not None and not lot.concept_id.startswith("ING-"):
            raise StateError(f"concept ids must start with ING-: {lot.concept_id}")
        e = Entity(lot.entity_id, lot.concept_id, lot.label, status, parents,
                   ev.event_id, quantity=quantity, location=ev.location)
        e.new_version(ev)
        self.entities[lot.entity_id] = e
        return e

    def _edge(self, rel: Relation, src: Iterable[str], dst: Iterable[str], ev: Event):
        self.edges.append((rel.value, tuple(src), tuple(dst), ev.event_id))

    def _set_belief(self, ent: Entity, b: Belief):
        cur = ent.fields.get(b.field)
        if (cur is not None and cur.trajectory == Trajectory.OBSERVED_SESSION
                and b.trajectory != Trajectory.OBSERVED_SESSION):
            # observation outranks plan/prediction: keep the observed value current
            ent.audit.setdefault(b.field, []).append(("SHADOWED_BY_OBSERVATION", b))
            return
        if cur is not None:
            reason = ("OVERRIDDEN_BY_OBSERVATION"
                      if b.trajectory == Trajectory.OBSERVED_SESSION else "SUPERSEDED")
            ent.audit.setdefault(b.field, []).append((reason, cur))
        ent.fields[b.field] = b

    @staticmethod
    def _sum(qs: list[Optional[Quantity]]) -> Optional[Quantity]:
        if not qs or any(q is None for q in qs):
            return None
        terms: tuple[Term, ...] = ()
        for q in qs:
            terms += q.terms
        return Quantity(terms)

    def _allocate(self, parent: Entity, lots: tuple[NewLot, ...]) -> list[Optional[Quantity]]:
        """Explicit amounts and stated fractions; at most one unspecified remainder."""
        fr = [l.fraction for l in lots if l.fraction is not None]
        if sum(fr) > 1.0 + 1e-9:
            raise StateError(f"fractions sum to {sum(fr):.3f} > 1 for {parent.entity_id}")
        unspecified = [k for k, l in enumerate(lots) if l.quantity is None and l.fraction is None]
        out: list[Optional[Quantity]] = []
        explicit: list[Amount] = []
        for l in lots:
            if l.quantity is not None:
                out.append(l.quantity)
                for t in l.quantity.terms:
                    explicit.append(t.amount)
            elif l.fraction is not None:
                out.append(parent.quantity.scaled(l.fraction) if parent.quantity else None)
            else:
                out.append(None)
        if len(unspecified) == 1 and parent.quantity is not None:
            k = unspecified[0]
            # Fractions are exact and correlated with the parent: the remainder of
            # "use half" is (1 - 1/2) x parent, NOT parent - half (which interval
            # arithmetic would widen). Explicit amounts stay symbolic subtractions.
            base = parent.quantity.scaled(1.0 - sum(fr)) if fr else parent.quantity
            out[k] = base.minus(*explicit) if explicit else base
        # conservation check, only where it is decidable without unit conversion
        pr = parent.quantity.resolved() if parent.quantity is not None else None
        if pr is not None:
            alloc = [q.resolved() for q in out if q is not None]
            if alloc and all(a is not None and a.unit == pr.unit for a in alloc):
                lo_total = sum(a.bounds[0] for a in alloc)
                if lo_total > pr.bounds[1] + 1e-9:
                    raise StateError(f"allocations ({lo_total:g} {pr.unit}) exceed "
                                     f"{parent.entity_id} ({pr.bounds[1]:g} {pr.unit})")
                if any(a.bounds[1] < -1e-9 for a in alloc):
                    raise StateError(f"negative remainder when splitting {parent.entity_id}")
        return out

    # ------------------------------------------------------------- apply
    def apply(self, ev: Event) -> None:
        if ev.event_id in self.event_ids:
            raise StateError(f"duplicate event id {ev.event_id}")
        if self.last_order is not None and ev.order <= self.last_order:
            raise StateError(f"event {ev.event_id} order {ev.order} ≤ previous {self.last_order}")
        snapshot = copy.deepcopy((self.entities, self.edges, self.candidates))
        try:
            self._dispatch(ev)
        except StateError:
            # leave the graph untouched by a rejected event
            self.entities, self.edges, self.candidates = snapshot
            raise
        self.event_ids.add(ev.event_id)
        self.last_order = ev.order

    def _dispatch(self, ev: Event) -> None:
        op = ev.op
        if op == Op.CREATE:
            if ev.inputs or not ev.outputs:
                raise StateError("CREATE takes no inputs and ≥1 output")
            for lot in ev.outputs:
                self._create(lot, (), ev, lot.quantity)

        elif op == Op.TRANSFORM:
            if len(ev.inputs) != 1 or ev.outputs:
                raise StateError("TRANSFORM keeps identity: exactly 1 input, no outputs")
            ent = self._usable(ev.inputs[0])
            before = ent.versions[-1][0]
            after = ent.new_version(ev)
            self.edges.append((Relation.TRANSFORMS_INTO.value, (before,), (after,), ev.event_id))
            if ev.belief is not None:
                self._set_belief(ent, ev.belief)

        elif op in (Op.MERGE, Op.RECOMBINE):
            if len(ev.inputs) < 2 or len(ev.outputs) != 1:
                raise StateError(f"{op.value} needs ≥2 inputs and exactly 1 output")
            ins = [self._usable(i) for i in ev.inputs]
            if op == Op.RECOMBINE and not any(e.status == RESERVED for e in ins):
                raise StateError("RECOMBINE needs at least one RESERVED input")
            if op == Op.MERGE and any(e.status == RESERVED for e in ins):
                raise StateError("a RESERVED lot rejoins via RECOMBINE, not MERGE")
            lot = ev.outputs[0]
            q = lot.quantity if lot.quantity is not None else self._sum([e.quantity for e in ins])
            self._create(lot, tuple(ev.inputs), ev, q)
            rel = Relation.MERGES_INTO if op == Op.MERGE else Relation.RECOMBINED_WITH
            self._edge(rel, ev.inputs, (lot.entity_id,), ev)
            for e in ins:
                e.status = CONSUMED

        elif op in (Op.SPLIT, Op.RESERVE):
            if len(ev.inputs) != 1 or len(ev.outputs) < 2:
                raise StateError(f"{op.value} needs exactly 1 input and ≥2 outputs")
            if op == Op.RESERVE and len(ev.outputs) != 2:
                raise StateError("RESERVE = [reserved portion, rest]")
            parent = self._usable(ev.inputs[0], allow={ACTIVE})
            qs = self._allocate(parent, ev.outputs)
            for k, (lot, q) in enumerate(zip(ev.outputs, qs, strict=True)):
                status = RESERVED if (op == Op.RESERVE and k == 0) else ACTIVE
                child = self._create(lot, (parent.entity_id,), ev, q, status=status)
                # a portion of melted butter is still melted: children inherit the
                # parent's current beliefs (same Belief objects, so provenance and the
                # originating event are preserved). Audit history stays with the parent.
                child.fields = dict(parent.fields)
            if op == Op.RESERVE:
                self._edge(Relation.RESERVED_AS, (parent.entity_id,), (ev.outputs[0].entity_id,), ev)
                self._edge(Relation.SPLITS_INTO, (parent.entity_id,), (ev.outputs[1].entity_id,), ev)
            else:
                self._edge(Relation.SPLITS_INTO, (parent.entity_id,),
                           tuple(l.entity_id for l in ev.outputs), ev)
            parent.status = CONSUMED

        elif op == Op.DISCARD:
            if not ev.inputs or ev.outputs:
                raise StateError("DISCARD takes ≥1 input and no outputs")
            for i in ev.inputs:
                e = self._usable(i)
                e.status = DISCARDED
                e.new_version(ev)
            self._edge(Relation.DISCARDED_FROM, ev.inputs, (), ev)

        elif op == Op.TRANSFER:
            if not ev.inputs or not ev.location:
                raise StateError("TRANSFER needs ≥1 input and a location")
            for i in ev.inputs:
                e = self._usable(i)
                e.location = ev.location
                e.new_version(ev)
            self._edge(Relation.TRANSFERRED_TO, ev.inputs, (ev.location,), ev)
            self._edge(Relation.LOCATED_IN, ev.inputs, (ev.location,), ev)

        elif op in (Op.SET_FIELD, Op.OBSERVE):
            if len(ev.inputs) != 1 or ev.belief is None:
                raise StateError(f"{op.value} needs exactly 1 input and a belief")
            b = ev.belief
            if op == Op.OBSERVE and b.trajectory != Trajectory.OBSERVED_SESSION:
                raise StateError("OBSERVE beliefs must have trajectory OBSERVED_SESSION")
            if op == Op.SET_FIELD and b.trajectory == Trajectory.OBSERVED_SESSION:
                raise StateError("use OBSERVE for observed values")
            if (b.provenance in (Provenance.MODEL_ESTIMATED, Provenance.IMPUTED,
                                 Provenance.SIMULATED, Provenance.INFERRED_LLM, Provenance.UNKNOWN)
                    and b.trajectory != Trajectory.PREDICTED):
                raise StateError(f"{b.provenance.value} may only back a PREDICTED belief (law B3)")
            ent = self._usable(ev.inputs[0])
            self._set_belief(ent, b)
            if op == Op.OBSERVE:
                self._edge(Relation.OBSERVED_AS, ev.inputs, (b.field,), ev)

        elif op == Op.OMITTED_STEP_CANDIDATE:
            if not ev.candidate_id or ev.proposed is None or not ev.rationale:
                raise StateError("a candidate needs candidate_id, a proposed event and a rationale")
            if ev.candidate_id in self.candidates:
                raise StateError(f"candidate {ev.candidate_id} already exists")
            self.candidates[ev.candidate_id] = {
                "status": "PROPOSED", "rationale": ev.rationale,
                "proposed_op": ev.proposed.op.value, "proposed_event_id": ev.proposed.event_id,
                "raised_by": ev.event_id, "_proposed": ev.proposed}

        elif op in (Op.ACCEPT_CANDIDATE, Op.REJECT_CANDIDATE):
            c = self.candidates.get(ev.candidate_id or "")
            if c is None or c["status"] != "PROPOSED":
                raise StateError(f"candidate {ev.candidate_id} is not PROPOSED")
            if op == Op.ACCEPT_CANDIDATE:
                self._dispatch(c["_proposed"])   # validated against the current state
                c["status"] = "ACCEPTED"
            else:
                c["status"] = "REJECTED"
            c["decided_by"] = ev.event_id
        else:  # pragma: no cover
            raise StateError(f"unsupported op {op}")

    # ------------------------------------------------------- serialisation
    def to_dict(self) -> dict:
        return {
            "entities": {k: v.to_dict() for k, v in sorted(self.entities.items())},
            "edges": [list(e) for e in self.edges],
            "candidates": {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
                           for k, v in sorted(self.candidates.items())},
            "events_applied": len(self.event_ids),
        }

    def digest(self) -> str:
        blob = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    # convenience for tests / callers
    def entity(self, eid: str) -> Entity:
        return self.entities[eid]

    def active(self) -> list[str]:
        return sorted(k for k, v in self.entities.items() if v.status in USABLE)


def replay(events: Iterable[Event]) -> StateGraph:
    """Pure fold: the only way state is produced."""
    g = StateGraph()
    for ev in events:
        g.apply(ev)
    return g


class EventLog:
    """Append-only event store. There is no update or delete."""

    def __init__(self, events: Iterable[Event] = ()):
        self._events: list[Event] = []
        self._state = StateGraph()
        for e in events:
            self.append(e)

    def append(self, ev: Event) -> None:
        self._state.apply(ev)          # raises StateError, leaving the log unchanged
        self._events.append(ev)

    @property
    def events(self) -> tuple[Event, ...]:
        return tuple(self._events)

    @property
    def state(self) -> StateGraph:
        return self._state
