r"""
Inter-annotator agreement for DEL-3 gold (brief RS-07-05), ID-invariant.

Each annotator names lots freely, so lots are canonicalised by *derivation*:
    created lot  → ("C", concept or normalised label)
    derived lot  → (op, process, sorted parent signatures, role)
where role distinguishes siblings of one split/reserve (reserved vs rest; for
plain splits: concept + stated quantity/fraction + rank). Metrics are then
computed on canonical tuples:

    event_f1            (step, op, process, input signatures)
    edge_f1             all §233.5 relation edges
    merge_split_f1      MERGES_INTO, SPLITS_INTO, RESERVED_AS, RECOMBINED_WITH, DISCARDED_FROM
    quantity_agreement  created lots: stated amount identical (raw/unit/value/interval)
    allocation_agreement derived lots: same symbolic quantity expression (or both unknown)
    field_agreement     final state fields with identical values

F1 is symmetric (A vs B). Disagreements are listed so they can drive guideline
revisions (Week-2 gate: "annotation disagreements produce handbook changes").
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .gold import GoldRecipe
from .model import Op

MS_RELATIONS = {"MERGES_INTO", "SPLITS_INTO", "RESERVED_AS", "RECOMBINED_WITH", "DISCARDED_FROM"}


def _norm(s: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(s).lower())).strip()


def _proc(ev) -> str:
    if ev.process_id:
        return ev.process_id[len("PROC-"):]
    return f"raw:{_norm(ev.process_raw)}" if ev.process_raw else ""


def signatures(g: GoldRecipe) -> dict[str, str]:
    """entity_id -> canonical, annotator-independent, human-readable signature.

    created:        butter
    merged:         MERGE:cook(butter, garlic)            (parents sorted)
    split/reserve:  RESERVE:reserve(butter).reserved
    """
    sig: dict[str, str] = {}
    for ev in g.events:
        if ev.op == Op.CREATE:
            for lot in ev.outputs:
                name = lot.concept_id[len("ING-"):] if lot.concept_id else _norm(lot.label)
                sig[lot.entity_id] = name
        elif ev.op in (Op.MERGE, Op.RECOMBINE):
            parents = ", ".join(sorted(sig[i] for i in ev.inputs))
            sig[ev.outputs[0].entity_id] = f"{ev.op.value}:{_proc(ev)}({parents})"
        elif ev.op in (Op.SPLIT, Op.RESERVE):
            parent = sig[ev.inputs[0]]
            if ev.op == Op.RESERVE:
                roles = ["reserved", "rest"]
            else:
                keys = [(lot.concept_id or "", lot.quantity.render() if lot.quantity else "",
                         "" if lot.fraction is None else f"{lot.fraction:g}") for lot in ev.outputs]
                seen: Counter = Counter()
                roles = []
                for k in keys:
                    roles.append("/".join(x for x in k if x) + (f"#{seen[k]}" if keys.count(k) > 1 else ""))
                    seen[k] += 1
            for lot, role in zip(ev.outputs, roles, strict=True):
                sig[lot.entity_id] = f"{ev.op.value}:{_proc(ev)}({parent}).{role}"
    return sig


def _f1(a: Counter, b: Counter) -> dict:
    tp = sum((a & b).values())
    na, nb = sum(a.values()), sum(b.values())
    p = tp / nb if nb else 1.0
    r = tp / na if na else 1.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    if na == 0 and nb == 0:
        f = 1.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4),
            "a_only": sorted((a - b).elements())[:20],
            "b_only": sorted((b - a).elements())[:20]}


def _events(g: GoldRecipe, sig) -> Counter:
    c = Counter()
    for ev in g.events:
        if ev.op in (Op.CREATE,):
            continue
        ins = ", ".join(sorted(sig.get(i, i) for i in ev.inputs))
        c[f"step {g.step_of.get(ev.event_id)}: {ev.op.value}:{_proc(ev)}({ins})"] += 1
    return c


def _edges(g: GoldRecipe, sig, only: set | None = None) -> Counter:
    def canon(x: str) -> str:
        m = re.match(r"STATE-(ENTITY-.+)-v(\d+)$", x)
        if m:
            return f"{sig.get(m.group(1), m.group(1))}@v{m.group(2)}"
        return sig.get(x, _norm(x))
    c = Counter()
    for rel, src, dst, _eid in g.graph.edges:
        if only and rel not in only:
            continue
        c[f"{rel}: [{', '.join(sorted(map(canon, src)))}] -> [{', '.join(sorted(map(canon, dst)))}]"] += 1
    return c


def _amount_key(q):
    if q is None:
        return None
    return tuple(sorted((t.sign, str(t.amount.unit), repr(t.amount.value), repr(t.amount.lo),
                         repr(t.amount.hi)) for t in q.terms))


def agreement(a: GoldRecipe, b: GoldRecipe) -> dict:
    if a.recipe_id != b.recipe_id:
        raise ValueError(f"different recipes: {a.recipe_id} vs {b.recipe_id}")
    sa, sb = signatures(a), signatures(b)
    inv_a = {v: k for k, v in sa.items()}
    inv_b = {v: k for k, v in sb.items()}
    common = set(inv_a) & set(inv_b)
    union = set(inv_a) | set(inv_b)

    created = [s for s in union if "(" not in s]
    q_ok = sum(1 for s in created if s in common and
               _amount_key(a.graph.entity(inv_a[s]).quantity) == _amount_key(b.graph.entity(inv_b[s]).quantity))
    derived = [s for s in union if "(" in s]
    alloc_ok = sum(1 for s in derived if s in common and
                   _amount_key(a.graph.entity(inv_a[s]).quantity) == _amount_key(b.graph.entity(inv_b[s]).quantity))

    fa, fb = {}, {}
    for s in common:
        for f, bel in a.graph.entity(inv_a[s]).fields.items():
            fa[(s, f)] = (bel.value, bel.unit, bel.trajectory.value)
        for f, bel in b.graph.entity(inv_b[s]).fields.items():
            fb[(s, f)] = (bel.value, bel.unit, bel.trajectory.value)
    fkeys = set(fa) | set(fb)
    f_ok = sum(1 for k in fkeys if fa.get(k) == fb.get(k))

    return {
        "recipe_id": a.recipe_id, "annotators": [a.annotator, b.annotator],
        "lots": {"a": len(sa), "b": len(sb), "matched": len(common), "union": len(union)},
        "event_f1": _f1(_events(a, sa), _events(b, sb)),
        "edge_f1": _f1(_edges(a, sa), _edges(b, sb)),
        "merge_split_f1": _f1(_edges(a, sa, MS_RELATIONS), _edges(b, sb, MS_RELATIONS)),
        "quantity_agreement": round(q_ok / len(created), 4) if created else 1.0,
        "allocation_agreement": round(alloc_ok / len(derived), 4) if derived else 1.0,
        "field_agreement": round(f_ok / len(fkeys), 4) if fkeys else 1.0,
        "unmatched_lots": {"a_only": sorted(set(inv_a) - set(inv_b))[:20],
                           "b_only": sorted(set(inv_b) - set(inv_a))[:20]},
    }
