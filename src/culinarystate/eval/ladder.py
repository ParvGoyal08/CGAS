r"""
K13 — DEL-5 baseline ladder B0–B5 (proposal §4 D5; SSOT §245.12; v4.0 AI9).

  B0  LLM only
  B1  dense RAG            (LSA top-k evidence as plain chunks)
  B2  BM25 + dense         (fused)
  B3  + structured         (weighted fusion with structured retrieval)
  B4  + state              (replayed session state from the DEL-3 engine added to the context)
  B5  + evidence routing   (compiled packet AO1; deterministic evidence class + policy decide
                            ANSWER / ASK / ABSTAIN *before* the LLM; the LLM only verbalises)

Every system returns {answer, mode, cited}. Citations are [EVD-xxxxxx] ids. B5's packet
lists DISALLOWED CLAIMS so the model cannot exceed evidence precision (§242.7).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from ..decision.core import relevance_gate, route
from ..llm.client import TemplateVerbaliser
from ..retrieval.core import (EvidenceIndex, Policy, Query, compatibility, confidence_vector,
                              evidence_class, precision_policy)

SYSTEM = ("You are a cooking-science assistant. Answer in at most 3 sentences. When evidence is given, "
          "cite the evidence ids you use in square brackets like [EVD-000123]. Do not invent numbers.")


@dataclass
class Item:
    id: str
    task_type: str
    question: str
    query: Optional[Query] = None
    session_state: Optional[str] = None      # rendered state from the DEL-3 engine
    gold: dict = field(default_factory=dict)


def _chunks(index: EvidenceIndex, ranked) -> str:
    lines = []
    for i, _ in ranked[:5]:
        a = index.atoms[i]
        val = "unknown" if a.value is None else (f"≥{a.lo:g}%" if a.censored == "RIGHT" else f"{a.value:g}%")
        lines.append(f"[{a.evidence_id}] {a.record['ingredient_raw']} — {a.target}: retention {val}")
    return "\n".join(lines)


def _packet(item: Item, index, ranked, hits, ecls, decision) -> str:
    sup = [a for a, v in hits if v["target"] == "MATCH"][:5]
    direct = [a for a, v in hits if v["food"] == "MATCH" and v["process"] == "MATCH" and v["target"] == "MATCH"]
    near = [a for a, v in hits if a not in direct and v["target"] == "MATCH" and v["process"] == "MATCH"]
    fmt = lambda a: f"[{a.evidence_id}] {a.record['ingredient_raw']} — {a.target}: " + \
        ("≥97.5% (capped at 100 in source)" if a.censored == "RIGHT" else f"{a.value:g}% (±2.5, nearest 5%)")
    return "\n".join([
        f"CURRENT STATE: {item.session_state or 'not provided'}",
        f"QUESTION: {item.question}",
        "DIRECT EVIDENCE:\n" + ("\n".join(fmt(a) for a in direct[:3]) or "none"),
        "NEAR EVIDENCE:\n" + ("\n".join(fmt(a) for a in near[:3]) or "none"),
        "CONDITION DIFFERENCES: source states preparation methods only; temperatures are UNKNOWN",
        "CONFLICTS: " + ("yes — report both" if ecls == "conflict" else "none detected"),
        "MODEL ESTIMATES: none used",
        f"EVIDENCE CLASS: {ecls}; DECISION: {decision}",
        f"ALLOWED PRECISION: {precision_policy(ecls, [(a, None) for a in (direct or near or sup)] if (direct or near) else [])}",
        "DISALLOWED CLAIMS: exact values beyond the stated precision; temperatures; claims about foods/processes not listed",
        "CITATION MAP: " + ", ".join(a.evidence_id for a in (direct or near)[:5]),
    ])


def _support(hits) -> list:
    direct = [a for a, v in hits if v["food"] == "MATCH" and v["process"] == "MATCH" and v["target"] == "MATCH"]
    near = [a for a, v in hits if a not in direct and v["target"] == "MATCH" and v["process"] == "MATCH"]
    return (direct or near)[:5]


def _allowed(atoms) -> set:
    out = set()
    for a in atoms:
        if a.value is not None:
            out.add(a.value)
        if a.censored == "RIGHT":
            out |= {a.lo, 100.0}
    return out


def answer(system: str, item: Item, index: EvidenceIndex, llm, policy: Optional[Policy] = None,
           guard: bool = True) -> dict:
    """guard=False gives the 'B5-noguard' ablation (no citation map, no numeric claim guard)."""
    q = item.query or Query(item.question)
    if system == "B0":
        return {"answer": llm.generate(SYSTEM, item.question, tag=f"{item.id}:B0"), "mode": "ANSWER", "cited": []}
    use = {"B1": ("dense",), "B2": ("bm25", "dense")}.get(system, ("structured", "bm25", "dense"))
    ranked = index.search(q, k=10, use=use)
    if system in ("B1", "B2", "B3", "B4"):
        ctx = _chunks(index, ranked)
        if system == "B4" and item.session_state:
            ctx = f"CURRENT STATE: {item.session_state}\n" + ctx
        out = llm.generate(SYSTEM, f"Evidence:\n{ctx}\n\nQuestion: {item.question}", tag=f"{item.id}:{system}")
        return {"answer": out, "mode": "ANSWER", "cited": re.findall(r"EVD-\d{6}", out)}
    # B5
    hits = [(index.atoms[i], compatibility(q, index.atoms[i], index.fam)) for i, _ in ranked]
    ecls, support = evidence_class(q, hits)
    foods = {a.ingredient_id for a in index.atoms}
    procs = {p for a in index.atoms for p in a.processes + a.alternatives}
    vec = confidence_vector(q, ranked, support or hits, ecls,
                            {"food": q.ingredient_id in foods, "process": set(q.processes) <= procs})
    decision = policy.decide(vec, ecls) if policy else ("ABSTAIN" if ecls == "unsupported" else "ANSWER")
    mode = route(item.question, ecls)
    if decision == "ABSTAIN" or mode == "ABSTAIN":
        return {"answer": "I don't have evidence that covers this food, process and nutrient, so I won't guess. "
                          f"({precision_policy('unsupported', [])})", "mode": "ABSTAIN", "cited": [],
                "evidence_class": ecls}
    packet = _packet(item, index, ranked, hits, ecls, decision)
    out = llm.generate(SYSTEM + " Use ONLY the packet. Respect ALLOWED PRECISION and DISALLOWED CLAIMS.",
                       packet, tag=f"{item.id}:B5")
    fallback = False
    if guard:
        sup = _support(hits)
        ok = _allowed(sup)
        if any(not any(abs(n - v) <= 2.5 for v in ok) for n in percent_claims(out)):
            out, fallback = TemplateVerbaliser().generate("", packet), True     # claim guard (§242.7)
        if not re.findall(r"EVD-\d{6}", out) and sup:
            out += " Sources: " + ", ".join(f"[{a.evidence_id}]" for a in sup[:3])  # deterministic citation map
    return {"answer": out, "mode": mode if decision == "ANSWER" else decision,
            "cited": re.findall(r"EVD-\d{6}", out), "evidence_class": ecls,
            "gate": relevance_gate(item.question), "guard_fallback": fallback}


# precision / censoring wording that the B5 packet itself prescribes — not value claims
_PRECISION_PHRASES = re.compile(
    r"(nearest\s+5\s*%|±\s*2\.5\s*%?|capped at 100\s*%?|cap(ped)? (of|at) 100\s*%|above 100\s*%|100\s*% cap)", re.I)


def percent_claims(text: str) -> list[float]:
    """Numbers stated as percentages, after (1) re-joining tokeniser splits like '97. 5%' and
    (2) removing the precision/censoring phrases the packet prescribes (scorer v1, DEC-023)."""
    t = re.sub(r"(\d)\.\s+(\d)", r"\1.\2", text)
    t = _PRECISION_PHRASES.sub(" ", t)
    return [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*%", t)]


def score(item: Item, res: dict, index: EvidenceIndex) -> dict:
    """Automatic metrics only; claim support is judged by humans (v4.0 AH14). Scorer v1."""
    ids = {a.evidence_id: a for a in index.atoms}
    cited = [c for c in res["cited"] if c in ids]
    fake = [c for c in res["cited"] if c not in ids]
    must_abstain = item.gold.get("must_abstain", False)
    req = set(item.gold.get("required_evidence_ids", []))
    nums = percent_claims(res["answer"])
    allowed = set()
    for c in cited:
        a = ids[c]
        if a.value is not None:
            allowed.add(a.value)
        if a.censored == "RIGHT":
            allowed |= {a.lo, 100.0}
    unsupported_numbers = [n for n in nums if not any(abs(n - v) <= 2.5 for v in allowed)]
    return {
        "abstained": res["mode"] == "ABSTAIN",
        "abstention_correct": (res["mode"] == "ABSTAIN") == must_abstain,
        "fabricated_citations": len(fake),
        "required_evidence_recall": (len(req & set(cited)) / len(req)) if req else None,
        "required_evidence_hit": (bool(req & set(cited))) if req else None,
        "percent_claims": len(nums),
        "unsupported_percent_claims": len(unsupported_numbers),
        "scorer_version": "v1",
    }
