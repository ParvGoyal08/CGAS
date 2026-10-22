r"""
Lossless JSON round-trip for events, so a session can be stored as plain data
and replayed later (SSOT §233.3: session continuation without prose chat history).
"""
from __future__ import annotations

from typing import Any, Optional

from .model import Amount, Belief, Event, NewLot, Op, Provenance, Quantity, Term, Trajectory


def _amount(d: dict) -> Amount:
    return Amount(raw=d["raw"], unit=d.get("unit"), value=d.get("value"),
                  lo=d.get("lo"), hi=d.get("hi"))


def _quantity_to(q: Optional[Quantity]) -> Optional[list]:
    if q is None:
        return None
    return [{"sign": t.sign, **t.amount.to_dict()} for t in q.terms]


def _quantity_from(d: Optional[list]) -> Optional[Quantity]:
    if d is None:
        return None
    return Quantity(tuple(Term(x["sign"], _amount(x)) for x in d))


def event_to_dict(e: Event) -> dict[str, Any]:
    return {
        "event_id": e.event_id, "order": e.order, "op": e.op.value,
        "inputs": list(e.inputs),
        "outputs": [{"entity_id": l.entity_id, "concept_id": l.concept_id, "label": l.label,
                     "quantity": _quantity_to(l.quantity), "fraction": l.fraction}
                    for l in e.outputs],
        "process_id": e.process_id, "process_raw": e.process_raw, "location": e.location,
        "belief": e.belief.to_dict() if e.belief else None,
        "candidate_id": e.candidate_id,
        "proposed": event_to_dict(e.proposed) if e.proposed else None,
        "rationale": e.rationale, "trajectory": e.trajectory.value,
        "provenance": e.provenance.value, "source_span": e.source_span,
    }


def event_from_dict(d: dict[str, Any]) -> Event:
    b = d.get("belief")
    belief = None if b is None else Belief(
        field=b["field"], value=b["value"], trajectory=Trajectory(b["trajectory"]),
        provenance=Provenance(b["provenance"]), event_id=b["event_id"], unit=b.get("unit"),
        lo=b.get("lo"), hi=b.get("hi"), evidence_ref=b.get("evidence_ref"),
        unknown=b.get("unknown", False))
    return Event(
        event_id=d["event_id"], order=d["order"], op=Op(d["op"]), inputs=tuple(d["inputs"]),
        outputs=tuple(NewLot(entity_id=o["entity_id"], concept_id=o["concept_id"],
                             label=o["label"], quantity=_quantity_from(o["quantity"]),
                             fraction=o["fraction"]) for o in d["outputs"]),
        process_id=d.get("process_id"), process_raw=d.get("process_raw"),
        location=d.get("location"), belief=belief, candidate_id=d.get("candidate_id"),
        proposed=event_from_dict(d["proposed"]) if d.get("proposed") else None,
        rationale=d.get("rationale"), trajectory=Trajectory(d["trajectory"]),
        provenance=Provenance(d["provenance"]), source_span=d.get("source_span"))
