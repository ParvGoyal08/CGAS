r"""
DEL-4 — evidence-aware retrieval, compatibility, evidence classes, confidence, policy.

Pipeline (SSOT §241–242, v4.0 AO1–AO2):
  structured filter + BM25 + dense (LSA = TF-IDF→SVD; labelled, not a neural encoder)
  → reciprocal-rank fusion (k = 60)
  → inspectable compatibility vector per candidate (12 axes; UNKNOWN is NEUTRAL, never a mismatch)
  → evidence class for the query (observed / near / interpolated / model-estimated /
    qualitative / conflict / unsupported)
  → confidence vector → calibrated P(supported) → ANSWER / ASK / ABSTAIN
Output precision never exceeds evidence precision (§242.7).
"""
from __future__ import annotations

import csv
import json
import math
import pathlib
import re
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = pathlib.Path(__file__).resolve().parents[3]
MATCH, NEAR, MISMATCH, UNKNOWN = "MATCH", "NEAR", "MISMATCH", "UNKNOWN"
AXES = ("food", "state", "process", "time", "temperature", "pH", "aw_moisture", "medium",
        "geometry", "target", "basis", "source_tier")


def _tok(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower().replace("proc-", " ").replace("ing-", " ").replace("-", " "))


# ------------------------------------------------------------------ atoms
@dataclass
class Atom:
    evidence_id: str
    ingredient_id: str
    food_group: Optional[str]
    state_in: Optional[str]
    processes: tuple
    alternatives: tuple
    target_code: str
    target: str
    nclass: str
    value: Optional[float]
    lo: Optional[float]
    hi: Optional[float]
    unit: Optional[str]
    censored: str
    tier: str
    source_id: str
    conditions: dict
    text: str
    record: dict = field(repr=False, default_factory=dict)


def load_atoms(ledger: pathlib.Path = ROOT / "ledgers/evidence/evidence_v0.jsonl") -> list[Atom]:
    fam = {}
    with (ROOT / "ledgers/process/proc_v0.csv").open() as fh:
        for r in csv.DictReader(fh):
            fam[r["proc_id"]] = r["family_id"]
    atoms = []
    for line in ledger.open():
        d = json.loads(line)
        if d["defect"] is not None:
            continue
        nclass = next((x.split("=")[1] for x in (d["notes"] or "").split("; ") if x.startswith("nutrient_class=")), "other")
        procs = tuple(d["process_ids"])
        alts = tuple(d["process_alternatives"])
        words = " ".join(p.replace("PROC-", "") for p in procs + alts)
        text = (f"{d['ingredient_id'].replace('ING-', '').replace('-', ' ')} {d['ingredient_raw'].lower()} "
                f"{d['food_form'] or ''} {d['state_in'] or ''} {words} {d['target_variable']} {nclass}")
        atoms.append(Atom(d["evidence_id"], d["ingredient_id"], d["food_group"], d["state_in"], procs, alts,
                          d["target_code"], d["target_variable"], nclass, d["value"], d["lo"], d["hi"],
                          d["unit"], d["censoring"], d["tier"], d["source_id"], d["conditions"], text, d))
    atoms_fam = fam
    for a in atoms:
        a.record["_families"] = sorted({atoms_fam.get(p, "") for p in a.processes + a.alternatives})
    return atoms


# ------------------------------------------------------------------ query
@dataclass
class Query:
    text: str
    ingredient_id: Optional[str] = None
    food_group: Optional[str] = None
    state_in: Optional[str] = None
    processes: tuple = ()
    target_code: Optional[str] = None
    target_class: Optional[str] = None
    time_min: Optional[float] = None
    temperature_c: Optional[float] = None


# ------------------------------------------------------------------ index
class EvidenceIndex:
    def __init__(self, atoms: list[Atom], svd_dim: int = 64, seed: int = 0):
        self.atoms = atoms
        self.docs = [_tok(a.text) for a in atoms]
        self.bm25 = BM25Okapi(self.docs)
        self.tfidf = TfidfVectorizer(token_pattern=r"[a-z0-9]+")
        X = self.tfidf.fit_transform([a.text.lower() for a in atoms])
        self.svd = TruncatedSVD(n_components=min(svd_dim, X.shape[1] - 1), random_state=seed)
        Z = self.svd.fit_transform(X)
        self.Z = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-12)
        fam = {}
        with (ROOT / "ledgers/process/proc_v0.csv").open() as fh:
            for r in csv.DictReader(fh):
                fam[r["proc_id"]] = r["family_id"]
        self.fam = fam

    def bm25_rank(self, q: Query, n: int) -> list[int]:
        s = self.bm25.get_scores(_tok(q.text))
        return list(np.argsort(-s)[:n])

    def dense_rank(self, q: Query, n: int) -> list[int]:
        z = self.svd.transform(self.tfidf.transform([q.text.lower()]))
        z = z / (np.linalg.norm(z) + 1e-12)
        s = self.Z @ z.ravel()
        return list(np.argsort(-s)[:n])

    def structured_rank(self, q: Query, n: int) -> list[int]:
        scores = []
        for a in self.atoms:
            sc = 0.0
            if q.target_code and a.target_code == q.target_code:
                sc += 4
            elif q.target_class and a.nclass == q.target_class:
                sc += 1
            if q.ingredient_id and a.ingredient_id == q.ingredient_id:
                sc += 3
            elif q.food_group and a.food_group == q.food_group:
                sc += 1
            if q.processes and set(q.processes) <= set(a.processes + a.alternatives):
                sc += 3
            elif q.processes and {self.fam.get(p) for p in q.processes} & set(a.record["_families"]):
                sc += 1
            scores.append(sc)
        s = np.array(scores)
        order = np.argsort(-s, kind="stable")
        return [int(i) for i in order[:n] if s[i] > 0]

    WEIGHTS = {"structured": 3.0, "bm25": 1.0, "dense": 1.0}   # dev decision DEC-021

    def search(self, q: Query, k: int = 10, n: int = 100, rrf_k: int = 60,
               use=("structured", "bm25", "dense")) -> list[tuple[int, float]]:
        ranks = {}
        if "structured" in use:
            ranks["structured"] = self.structured_rank(q, n)
        if "bm25" in use:
            ranks["bm25"] = self.bm25_rank(q, n)
        if "dense" in use:
            ranks["dense"] = self.dense_rank(q, n)
        fused: dict[int, float] = {}
        for name, lst in ranks.items():
            for r, i in enumerate(lst):
                fused[i] = fused.get(i, 0.0) + self.WEIGHTS.get(name, 1.0) / (rrf_k + r + 1)
        return sorted(fused.items(), key=lambda x: -x[1])[:k]


# ------------------------------------------------------------------ compatibility (AO2)
def compatibility(q: Query, a: Atom, fam: dict) -> dict[str, str]:
    v = {ax: UNKNOWN for ax in AXES}
    if q.ingredient_id:
        if a.ingredient_id == q.ingredient_id:
            v["food"] = MATCH
        elif q.food_group and a.food_group == q.food_group:
            v["food"] = NEAR
        elif set(q.ingredient_id.split("-")[1:]) & set(a.ingredient_id.split("-")[1:]):
            v["food"] = NEAR
        else:
            v["food"] = MISMATCH
    if q.state_in and a.state_in:
        v["state"] = MATCH if q.state_in == a.state_in else MISMATCH
    if q.processes:
        ap = set(a.processes) | set(a.alternatives)
        if set(q.processes) == set(a.processes) or (a.alternatives and set(q.processes) <= ap):
            v["process"] = MATCH
        elif set(q.processes) <= ap:
            v["process"] = NEAR
        elif {fam.get(p) for p in q.processes} & {fam.get(p) for p in ap}:
            v["process"] = NEAR
        else:
            v["process"] = MISMATCH
    t = (a.conditions or {}).get("t")
    if q.time_min is not None and t and t.get("status") in ("MEASURED", "RANGE"):
        lo = t["lo"] if t.get("lo") is not None else t["value"]
        hi = t["hi"] if t.get("hi") is not None else t["value"]
        if lo <= q.time_min <= hi:
            v["time"] = MATCH
        elif lo / 2 <= q.time_min <= hi * 2:
            v["time"] = NEAR
        else:
            v["time"] = MISMATCH
    T = (a.conditions or {}).get("T")
    if q.temperature_c is not None and T and T.get("status") in ("MEASURED", "RANGE"):
        v["temperature"] = MATCH  # refined once evidence with temperatures exists
    if q.target_code:
        v["target"] = MATCH if a.target_code == q.target_code else (NEAR if q.target_class == a.nclass else MISMATCH)
    elif q.target_class:
        v["target"] = NEAR if a.nclass == q.target_class else MISMATCH
    v["source_tier"] = MATCH if a.tier in ("E1", "E2", "E3", "E4") else NEAR
    return v


def compatible(v: dict, strict: bool) -> bool:
    """UNKNOWN is neutral. Strict = no NEAR on food/process/target."""
    core = [v["food"], v["process"], v["target"]]
    if any(x == MISMATCH for x in core):
        return False
    if any(v[ax] == MISMATCH for ax in ("time", "temperature", "state")):
        return False
    return all(x in (MATCH, UNKNOWN) for x in core) if strict else True


# ------------------------------------------------------------------ evidence class
CLASSES = ("observed", "near", "interpolated", "model-estimated", "qualitative", "conflict", "unsupported")


def _interval(a: Atom):
    lo = a.lo if a.lo is not None else a.value
    hi = a.hi if a.hi is not None else (math.inf if a.censored == "RIGHT" else a.value)
    return lo, hi


def evidence_class(q: Query, hits: list[tuple[Atom, dict]]) -> tuple[str, list]:
    direct = [(a, v) for a, v in hits if compatible(v, strict=True)
              and v["food"] == MATCH and v["process"] == MATCH and v["target"] == MATCH]
    if direct:
        ivs = [_interval(a) for a, _ in direct]
        lo, hi = max(i[0] for i in ivs), min(i[1] for i in ivs)
        if len(direct) > 1 and lo > hi:
            return "conflict", direct
        return "observed", direct
    # "near" needs the SAME process (dev decision DEC-021): family-level process similarity
    # (e.g. sous-vide vs canning, both thermal-wet) is too weak to support a retention answer
    near = [(a, v) for a, v in hits if compatible(v, strict=False) and v["target"] == MATCH
            and v["process"] == MATCH and v["food"] in (MATCH, NEAR)]
    if near:
        return "near", near
    qual = [(a, v) for a, v in hits if a.value is None and compatible(v, strict=False)]
    if qual:
        return "qualitative", qual
    return "unsupported", []


# ------------------------------------------------------------------ confidence vector (§242.1 subset)
LEVEL = {MATCH: 1.0, NEAR: 0.5, UNKNOWN: 0.5, MISMATCH: 0.0}


def confidence_vector(q: Query, ranked: list[tuple[int, float]], hits, ecls: str, in_vocab: dict) -> dict:
    top = hits[0][1] if hits else {ax: MISMATCH for ax in AXES}
    s = [x for _, x in ranked]
    margin = (s[0] - s[1]) / s[0] if len(s) > 1 and s[0] > 0 else (1.0 if s else 0.0)
    cond_axes = [top[a] for a in ("time", "temperature", "pH", "aw_moisture", "medium")]
    known = [c for c in cond_axes if c != UNKNOWN]
    vals = [a.value for a, _ in hits if a.value is not None and compatible(_, strict=True)] if hits else []
    return {
        "q_retrieval": float(min(1.0, s[0] * 61 / 5)) if s else 0.0,
        "q_margin": float(margin),
        "q_entity": LEVEL[top["food"]], "q_process": LEVEL[top["process"]], "q_target": LEVEL[top["target"]],
        "q_condition": (sum(LEVEL[c] for c in known) / len(known)) if known else 0.5,
        "q_source": 1.0 if hits and hits[0][0].tier in ("E1", "E2", "E3", "E4") else 0.0,
        "q_agreement": 0.0 if ecls == "conflict" else (1.0 if len(set(vals)) <= 1 else 1.0 / len(set(vals))),
        "q_ood": 0.0 if (in_vocab.get("food") and in_vocab.get("process")) else 1.0,
        "q_class_direct": 1.0 if ecls == "observed" else 0.0,
    }


class Policy:
    """Logistic calibration of the confidence vector → P(supported); thresholds set on dev."""

    def __init__(self, feats=None):
        self.feats = feats or ["q_retrieval", "q_margin", "q_entity", "q_process", "q_target",
                               "q_condition", "q_source", "q_agreement", "q_ood", "q_class_direct"]
        self.coef = None
        self.answer_t, self.ask_t = 0.7, 0.4

    def fit(self, vecs: list[dict], supported: list[int]):
        from sklearn.linear_model import LogisticRegression
        X = np.array([[v[f] for f in self.feats] for v in vecs])
        self.lr = LogisticRegression(max_iter=2000).fit(X, np.array(supported))
        return self

    def prob(self, vec: dict) -> float:
        X = np.array([[vec[f] for f in self.feats]])
        return float(self.lr.predict_proba(X)[0, 1])

    def decide(self, vec: dict, ecls: str) -> str:
        if ecls == "unsupported":
            return "ABSTAIN"
        if ecls == "conflict":
            return "ANSWER_WITH_CONFLICT"
        p = self.prob(vec)
        return "ANSWER" if p >= self.answer_t else ("ASK" if p >= self.ask_t else "ABSTAIN")


def precision_policy(ecls: str, hits) -> str:
    """§242.7: output precision ≤ evidence precision."""
    if ecls == "observed":
        a = hits[0][0]
        if a.censored == "RIGHT":
            return f"at least ~{a.lo:g}% retained (source caps reported values at 100%)"
        return f"{a.value:g}% retained (reported to the nearest 5%)"
    if ecls == "near":
        vals = [a.value for a, _ in hits if a.value is not None]
        return f"similar foods/processes: {min(vals):g}–{max(vals):g}% retained (range, not a point value)"
    if ecls == "conflict":
        return "sources disagree; both values reported with their conditions"
    return "no compatible evidence; abstain"
