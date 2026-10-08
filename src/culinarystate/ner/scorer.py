r"""
P14 — B08 common NER scorer + split/leakage audit (v4.0 AH11, AQ3, AW).

One scorer for every NER system we compare (rule baseline, LLM, any RecipeDB3 model
once permission arrives), so numbers are comparable by construction.

  Span = (doc_id, start, end, label), character offsets, end exclusive.
  exact    : same doc, start, end and label
  overlap  : same doc and label, character ranges intersect (each gold/pred matched at most once,
             greedy by largest overlap — a relaxed view, always reported NEXT TO exact, never instead)
  per-label P/R/F1, micro (pooled counts) and macro (mean over labels present in gold)

Leakage audit: normalised exact duplicates and near-duplicates (Jaccard on word 5-gram
shingles ≥ threshold) between train and test documents. External published numbers
stay "external" until rerun under this scorer (AW).
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    doc_id: str
    start: int
    end: int
    label: str

    def __post_init__(self):
        if not 0 <= self.start < self.end:
            raise ValueError(f"bad span {self}")


def _prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f}


def _match(gold: list[Span], pred: list[Span], mode: str) -> set[tuple[int, int]]:
    if mode == "exact":
        gi = {g: i for i, g in enumerate(gold)}
        return {(gi[p], j) for j, p in enumerate(pred) if p in gi}
    cand = []
    for i, g in enumerate(gold):
        for j, p in enumerate(pred):
            if g.doc_id == p.doc_id and g.label == p.label:
                ov = min(g.end, p.end) - max(g.start, p.start)
                if ov > 0:
                    cand.append((-ov, i, j))
    used_g, used_p, pairs = set(), set(), set()
    for _, i, j in sorted(cand):
        if i not in used_g and j not in used_p:
            used_g.add(i)
            used_p.add(j)
            pairs.add((i, j))
    return pairs


def score_spans(gold: list[Span], pred: list[Span]) -> dict:
    if len(set(gold)) != len(gold) or len(set(pred)) != len(pred):
        raise ValueError("duplicate spans")
    out = {}
    labels = sorted({s.label for s in gold} | {s.label for s in pred})
    for mode in ("exact", "overlap"):
        pairs = _match(gold, pred, mode)
        per = {}
        for lab in labels:
            tp = sum(1 for i, _ in pairs if gold[i].label == lab)
            per[lab] = _prf(tp, sum(1 for s in pred if s.label == lab) - tp, sum(1 for s in gold if s.label == lab) - tp)
        tp = len(pairs)
        gold_labels = {s.label for s in gold}
        out[mode] = {"micro": _prf(tp, len(pred) - tp, len(gold) - tp),
                     "macro_f1": (sum(per[lab]["f1"] for lab in gold_labels) / len(gold_labels)) if gold_labels else 0.0,
                     "per_label": per}
    return out


# ------------------------------------------------------------------ leakage audit
def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", t.lower())).strip()


def _shingles(t: str, n: int = 5) -> set:
    w = _norm(t).split()
    return {" ".join(w[i:i + n]) for i in range(max(1, len(w) - n + 1))}


def leakage_audit(train: dict[str, str], test: dict[str, str], jaccard: float = 0.8, n: int = 5) -> dict:
    """Exact (normalised) and near duplicates of test docs in train. Inverted index on shingles,
    so cost scales with shared shingles, not |train|×|test|."""
    norm_train = defaultdict(list)
    for k, t in train.items():
        norm_train[_norm(t)].append(k)
    sh_train = {k: _shingles(t, n) for k, t in train.items()}
    inv = defaultdict(set)
    for k, s in sh_train.items():
        for x in s:
            inv[x].add(k)
    exact, near = [], []
    for k, t in test.items():
        if _norm(t) in norm_train:
            exact.append((k, norm_train[_norm(t)][0]))
            continue
        s = _shingles(t, n)
        cands = set().union(*(inv[x] for x in s if x in inv)) if s else set()
        best = max(((len(s & sh_train[c]) / len(s | sh_train[c]), c) for c in cands), default=(0.0, None))
        if best[0] >= jaccard:
            near.append((k, best[1], round(best[0], 3)))
    return {"n_test": len(test), "exact_duplicates": exact, "near_duplicates": near,
            "leak_rate": (len(exact) + len(near)) / len(test) if test else 0.0, "jaccard": jaccard, "shingle_n": n}
