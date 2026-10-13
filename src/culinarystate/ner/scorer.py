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


# ------------------------------------------------------------------ beyond spans (P5B): one scorer for the cascade
# span → linking → attributes → relations/events → state graph. Event / edge / merge-split F1 and replay
# consistency between a gold and a predicted recipe graph live in culinarystate.state_graph.agreement
# (agreement(gold, pred)); this module covers the text-level layers.

def linking_metrics(gold: dict, pred: dict, k: int = 5) -> dict:
    """gold: mention_id → concept id; pred: mention_id → ranked list of concept ids ([] = abstained).
    Acc@1 and Recall@k are over ALL gold mentions (abstentions count as misses); abstain rate reported beside."""
    n = len(gold)
    if n == 0:
        return {"n": 0, "acc_at_1": 0.0, f"recall_at_{k}": 0.0, "abstain_rate": 0.0}
    a1 = sum(1 for m, g in gold.items() if (pred.get(m) or [])[:1] == [g])
    rk = sum(1 for m, g in gold.items() if g in (pred.get(m) or [])[:k])
    ab = sum(1 for m in gold if not pred.get(m))
    return {"n": n, "acc_at_1": a1 / n, f"recall_at_{k}": rk / n, "abstain_rate": ab / n}


def _norm_attr(v):
    if isinstance(v, (int, float)):
        return round(float(v), 6)
    if isinstance(v, (tuple, list)):
        return tuple(_norm_attr(x) for x in v)
    return re.sub(r"\s+", " ", str(v).strip().lower())


def attribute_accuracy(gold: dict, pred: dict) -> dict:
    """gold/pred: span_key → {attribute: value} (e.g. quantity=(2.0, 'UNIT-tbsp'), form='chopped', state='raw').
    Accuracy per attribute over GOLD spans that carry it; a missing prediction is wrong; values compared after
    light normalisation (numbers rounded, strings lower-cased) — no unit conversion is done here."""
    per = defaultdict(lambda: [0, 0])
    for key, attrs in gold.items():
        for a, v in attrs.items():
            per[a][1] += 1
            if _norm_attr((pred.get(key) or {}).get(a)) == _norm_attr(v):
                per[a][0] += 1
    return {a: {"correct": c, "n": n, "accuracy": c / n} for a, (c, n) in sorted(per.items())}


def relation_f1(gold: set, pred: set) -> dict:
    """gold/pred: sets of (head_id, relation, tail_id). Per-relation and micro P/R/F1."""
    rels = sorted({r for _, r, _ in gold | pred})
    out = {"per_relation": {}}
    for r in rels:
        g = {t for t in gold if t[1] == r}
        p = {t for t in pred if t[1] == r}
        out["per_relation"][r] = _prf(len(g & p), len(p - g), len(g - p))
    out["micro"] = _prf(len(gold & pred), len(pred - gold), len(gold - pred))
    return out


def frequency_strata(item_freq: dict, head_share: float = 0.2, tail_share: float = 0.5) -> dict:
    """Assign each item to head / mid / tail by corpus frequency rank (top 20% head, bottom 50% tail by default),
    so every metric can be reported per stratum (brief §8: errors stratified by ingredient frequency)."""
    order = sorted(item_freq, key=lambda k: (-item_freq[k], k))
    n = len(order)
    h, t = int(round(n * head_share)), int(round(n * (1 - tail_share)))
    return {k: ("head" if i < h else "tail" if i >= t else "mid") for i, k in enumerate(order)}
