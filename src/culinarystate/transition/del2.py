r"""
DEL-2 — sparsity-aware completion + cold-split benchmark, implementing the frozen
pre-registration experiments/DEL2/card.md (SHA in registry/preregistration.csv).

Everything here follows the card's letters:
  E  baselines D0–D5, D7 (FM with side information) + biased-MF comparator; D6 not run
  F  splits: pair-holdout (headline), ingredient-disjoint (headline), process-disjoint,
     random masked-cell (sanity only); 5 folds × seeds 20261008/09/10
  G  leakage audit: duplicate nutrient vectors grouped before splitting
  I  inner 3-fold CV for LightGBM and FM hyper-parameters, training folds only
  J  split-conformal on a calibration slice of each training fold (empirical coverage only)
  K  censor-aware MAE (truth 100 is right-censored: error = max(0, 100 − ŷ))
  N  grouped bootstrap 2,000 resamples; paired bootstrap for model differences
  R/S negative (permuted process) and positive (injected −20) controls
  SX-13-04 propensity: P(pair observed | food group, process family), IPS clipped at 0.05
"""
from __future__ import annotations

import csv
import itertools
import json
import pathlib
from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression

ROOT = pathlib.Path(__file__).resolve().parents[3]
SEEDS = (20261008, 20261009, 20261010)
N_FOLDS = 5
CENSOR = 100.0


# ------------------------------------------------------------------ data
def load_cells(ledger_jsonl: pathlib.Path) -> pd.DataFrame:
    """Evaluable R6 cells with the features named in card §E."""
    fam = {}
    with (ROOT / "ledgers/process/proc_v0.csv").open() as fh:
        for r in csv.DictReader(fh):
            fam[r["proc_id"]] = r["family_id"].replace("PROC-FAM-", "")
    recs = []
    for line in ledger_jsonl.open():
        d = json.loads(line)
        if d["defect"] is not None or d["tier"] not in ("E1", "E2", "E3", "E4"):
            continue
        procs = d["process_ids"] + d["process_alternatives"]
        sig = "|".join(d["process_ids"]) + ("~" + "/".join(d["process_alternatives"]) if d["process_alternatives"] else "")
        nclass = next((x.split("=")[1] for x in (d["notes"] or "").split("; ") if x.startswith("nutrient_class=")), "other")
        recs.append({
            "code": d["source_record"].split(";")[0].split("=")[1],
            "ingredient": d["ingredient_id"], "food_group": d["food_group"],
            "food_tokens": "|".join(filter(None, [d["ingredient_id"], d["food_form"], d["state_in"]])),
            "procs": "|".join(procs), "proc_sig": sig,
            "proc_fams": "|".join(sorted({fam.get(p, "UNMAPPED") for p in procs})),
            "nutrient": d["target_code"], "nclass": nclass,
            "y": float(d["value"]), "censored": d["censoring"] == "RIGHT",
        })
    return pd.DataFrame(recs)


# ------------------------------------------------------------------ metric (card K)
def censor_err(y: np.ndarray, yhat: np.ndarray, cens: np.ndarray) -> np.ndarray:
    e = np.abs(yhat - y)
    return np.where(cens, np.maximum(0.0, CENSOR - yhat), e)


# ------------------------------------------------------------------ leakage audit (card G)
def duplicate_clusters(cells: pd.DataFrame) -> dict[str, str]:
    """code → cluster id; codes whose full nutrient vectors are identical share a cluster."""
    vec = cells.pivot_table(index="code", columns="nutrient", values="y", aggfunc="first")
    key = vec.fillna(-1).astype(int).astype(str).agg(",".join, axis=1)
    cluster = {}
    for _k, codes in key.groupby(key).groups.items():
        cid = min(codes)
        for c in codes:
            cluster[c] = cid
    return cluster


def _union_groups(cells: pd.DataFrame, unit: str, cluster: dict) -> pd.Series:
    """Merge units connected by duplicate-vector clusters (union-find)."""
    parent = {u: u for u in cells[unit].unique()}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    by_cluster = cells.drop_duplicates("code").groupby(cells["code"].map(cluster))[unit].apply(set)
    for units in by_cluster:
        units = sorted(units)
        for u in units[1:]:
            parent[find(u)] = find(units[0])
    return cells[unit].map(find)


# ------------------------------------------------------------------ splits (card F)
def make_folds(cells: pd.DataFrame, split: str, seed: int, cluster: dict) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if split == "random":
        return rng.integers(0, N_FOLDS, len(cells))
    unit = {"pair": "code", "ingredient": "ingredient", "process": "proc_sig"}[split]
    groups = _union_groups(cells, unit, cluster) if split != "pair" else cells["code"].map(cluster)
    uniq = np.array(sorted(groups.unique()))
    rng.shuffle(uniq)
    fold_of = {g: k % N_FOLDS for k, g in enumerate(uniq)}
    return groups.map(fold_of).to_numpy()


def group_ids(cells: pd.DataFrame, split: str, cluster: dict) -> pd.Series:
    if split == "random":
        return cells.index.to_series().astype(str)
    unit = {"pair": "code", "ingredient": "ingredient", "process": "proc_sig"}[split]
    return _union_groups(cells, unit, cluster) if split != "pair" else cells["code"].map(cluster)


# ------------------------------------------------------------------ baselines (card E)
def d0(tr, te):
    return np.full(len(te), 100.0)


def d1(tr, te):
    m = tr.groupby("nutrient")["y"].mean()
    return te["nutrient"].map(m).fillna(tr["y"].mean()).to_numpy()


def d2(tr, te):
    m = tr.groupby(["proc_sig", "nutrient"])["y"].mean()
    key = list(zip(te["proc_sig"], te["nutrient"], strict=True))
    base = d1(tr, te)
    return np.array([m.get(k, b) for k, b in zip(key, base, strict=True)])


def d3(tr, te, k_shrink: float = 3.0):
    """Empirical-Bayes partial pooling of (food group × process) toward D2, per nutrient."""
    prior = d2(tr, te)
    g = tr.groupby(["food_group", "proc_sig", "nutrient"])["y"].agg(["mean", "count"])
    out = []
    for (fg, ps, nu), p in zip(zip(te["food_group"], te["proc_sig"], te["nutrient"], strict=True), prior, strict=True):
        if (fg, ps, nu) in g.index:
            mu, n = g.loc[(fg, ps, nu)]
            out.append((n * mu + k_shrink * p) / (n + k_shrink))
        else:
            out.append(p)
    return np.array(out)


def d4(tr, te):
    """Nearest evidence: same nutrient + process; most similar training food."""
    fallback = d2(tr, te)
    trg = tr.groupby(["proc_sig", "nutrient"])
    out = []
    for (_, row), fb in zip(te.iterrows(), fallback, strict=True):
        key = (row["proc_sig"], row["nutrient"])
        if key not in trg.groups:
            out.append(fb)
            continue
        cand = tr.loc[trg.groups[key]]
        toks = set(row["food_tokens"].split("|"))
        same_group = cand["food_group"] == row["food_group"]
        jac = cand["food_tokens"].map(lambda s: len(toks & set(s.split("|"))) / len(toks | set(s.split("|"))))  # noqa: B023 — evaluated immediately
        score = same_group.astype(float) * 10 + jac
        best = cand[score == score.max()]
        out.append(best["y"].mean())
    return np.array(out)


FEATS_ID = ["ingredient", "food_group", "food_tokens", "nutrient", "nclass"]
FEATS_PROC = ["procs", "proc_fams"]


def _design(tr, te, with_proc: bool):
    cols = FEATS_ID + (FEATS_PROC if with_proc else [])
    vocab = {}
    def rows(df):
        r, c = [], []
        for i, (_, row) in enumerate(df[cols].iterrows()):
            for col in cols:
                vals = str(row[col]).split("|") if col in ("food_tokens", "procs", "proc_fams") else [str(row[col])]
                for v in vals:
                    if not v:
                        continue
                    key = f"{col}={v}"
                    if key not in vocab:
                        if df is te:
                            continue          # unseen in training → no column (cold start)
                        vocab[key] = len(vocab)
                    r.append(i)
                    c.append(vocab[key])
        return r, c
    rtr, ctr = rows(tr)
    rte, cte = rows(te)
    n = len(vocab)
    Xtr = sparse.csr_matrix((np.ones(len(rtr)), (rtr, ctr)), shape=(len(tr), n))
    Xte = sparse.csr_matrix((np.ones(len(rte)), (rte, cte)), shape=(len(te), n))
    return Xtr, Xte


def d5(tr, te, with_proc=True, params=None, seed=0):
    params = params or {"num_leaves": 15, "n_estimators": 200}
    Xtr, Xte = _design(tr, te, with_proc)
    m = lgb.LGBMRegressor(learning_rate=0.05, num_leaves=params["num_leaves"],
                          n_estimators=params["n_estimators"], min_child_samples=5,
                          random_state=seed, verbose=-1)
    m.fit(Xtr.astype(np.float32), tr["y"].to_numpy())
    return m.predict(Xte.astype(np.float32))


@dataclass
class FM:
    rank: int = 4
    l2: float = 1e-2
    iters: int = 400
    lr: float = 0.05
    seed: int = 0

    def fit(self, X: sparse.csr_matrix, y: np.ndarray):
        rng = np.random.default_rng(self.seed)
        n, p = X.shape
        self.w0 = float(y.mean())
        self.w = np.zeros(p)
        self.V = rng.normal(0, 0.01, (p, self.rank))
        X2 = X.multiply(X)
        params = [self.w, self.V]
        m = [np.zeros_like(a) for a in params]
        v = [np.zeros_like(a) for a in params]
        b1, b2, eps = 0.9, 0.999, 1e-8
        for t in range(1, self.iters + 1):
            XV = X @ self.V
            pred = self.w0 + X @ self.w + 0.5 * ((XV ** 2).sum(1) - (X2 @ (self.V ** 2)).sum(1))
            r = (pred - y) / n
            gw = X.T @ r + self.l2 * self.w
            gV = (X.T @ (r[:, None] * XV)) - (X2.T @ r)[:, None] * self.V + self.l2 * self.V
            for k, (a, g) in enumerate(zip(params, (gw, gV), strict=True)):
                m[k] = b1 * m[k] + (1 - b1) * g
                v[k] = b2 * v[k] + (1 - b2) * g * g
                a -= self.lr * (m[k] / (1 - b1 ** t)) / (np.sqrt(v[k] / (1 - b2 ** t)) + eps)
        return self

    def predict(self, X):
        XV = X @ self.V
        return self.w0 + X @ self.w + 0.5 * ((XV ** 2).sum(1) - (X.multiply(X) @ (self.V ** 2)).sum(1))


def d7(tr, te, with_proc=True, params=None, seed=0):
    params = params or {"rank": 4, "l2": 1e-2}
    Xtr, Xte = _design(tr, te, with_proc)
    fm = FM(rank=params["rank"], l2=params["l2"], seed=seed).fit(Xtr, tr["y"].to_numpy())
    return np.asarray(fm.predict(Xte)).ravel()


def mf_biased(tr, te, rank=4, l2=1e-1, iters=300, seed=0):
    """Rows = retention code, columns = nutrient. Unseen rows fall back to biases only."""
    rows = {c: i for i, c in enumerate(sorted(tr["code"].unique()))}
    cols = {c: i for i, c in enumerate(sorted(set(tr["nutrient"]) | set(te["nutrient"])))}
    rng = np.random.default_rng(seed)
    P = rng.normal(0, 0.01, (len(rows), rank))
    Q = rng.normal(0, 0.01, (len(cols), rank))
    bu, bi, mu = np.zeros(len(rows)), np.zeros(len(cols)), tr["y"].mean()
    ri = tr["code"].map(rows).to_numpy()
    ci = tr["nutrient"].map(cols).to_numpy()
    y = tr["y"].to_numpy()
    lr = 0.1
    nr = np.maximum(np.bincount(ri, minlength=len(rows)), 1)[:, None]
    nc = np.maximum(np.bincount(ci, minlength=len(cols)), 1)[:, None]
    for _ in range(iters):
        pred = mu + bu[ri] + bi[ci] + (P[ri] * Q[ci]).sum(1)
        e = pred - y
        # per-parameter MEAN gradients (bug fix 2026-10-08: summed gradients diverged → NaN)
        gbu = np.bincount(ri, weights=e, minlength=len(rows)) / nr[:, 0] + l2 * bu
        gbi = np.bincount(ci, weights=e, minlength=len(cols)) / nc[:, 0] + l2 * bi
        gP = np.zeros_like(P)
        gQ = np.zeros_like(Q)
        np.add.at(gP, ri, e[:, None] * Q[ci])
        np.add.at(gQ, ci, e[:, None] * P[ri])
        bu -= lr * gbu
        bi -= lr * gbi
        P -= lr * (gP / nr + l2 * P)
        Q -= lr * (gQ / nc + l2 * Q)
    out = []
    for c, nu in zip(te["code"], te["nutrient"], strict=True):
        j = cols[nu]
        if c in rows:
            i = rows[c]
            out.append(mu + bu[i] + bi[j] + P[i] @ Q[j])
        else:
            out.append(mu + bi[j])
    return np.array(out)


# ------------------------------------------------------------------ inner CV (card I)
GRID = {
    "d5": [{"num_leaves": nl, "n_estimators": ne} for nl in (7, 15, 31) for ne in (200, 500)],
    "d7": [{"rank": r, "l2": l} for r in (2, 4, 8) for l in (1e-3, 1e-2, 1e-1)],
}


def inner_select(tr, kind, split, seed, cluster, with_proc):
    folds = make_folds(tr.reset_index(drop=True), split if split != "random" else "random", seed + 7, cluster) % 3
    trr = tr.reset_index(drop=True)
    best, best_err = None, np.inf
    fn = d5 if kind == "d5" else d7
    for params in GRID[kind]:
        errs = []
        for k in range(3):
            a, b = trr[folds != k], trr[folds == k]
            if len(b) == 0 or len(a) == 0:
                continue
            p = fn(a, b, with_proc=with_proc, params=params, seed=seed)
            errs.append(censor_err(b["y"].to_numpy(), p, b["censored"].to_numpy()).mean())
        e = float(np.mean(errs))
        if e < best_err:
            best, best_err = params, e
    return best


# ------------------------------------------------------------------ propensity (SX-13-04)
def propensity(cells: pd.DataFrame, interaction: bool) -> dict:
    pairs = cells.drop_duplicates("code")[["code", "ingredient", "food_group", "proc_sig", "proc_fams"]]
    ing_group = pairs.drop_duplicates("ingredient").set_index("ingredient")["food_group"]
    sig_fam = pairs.drop_duplicates("proc_sig").set_index("proc_sig")["proc_fams"]
    universe = pd.DataFrame(list(itertools.product(ing_group.index, sig_fam.index)), columns=["ingredient", "proc_sig"])
    universe["food_group"] = universe["ingredient"].map(ing_group)
    universe["proc_fams"] = universe["proc_sig"].map(sig_fam)
    observed = set(zip(pairs["ingredient"], pairs["proc_sig"], strict=True))
    universe["obs"] = [(i, s) in observed for i, s in zip(universe["ingredient"], universe["proc_sig"], strict=True)]
    feats = pd.get_dummies(universe["food_group"], prefix="g").join(
        universe["proc_fams"].str.get_dummies("|").add_prefix("f_"))
    if interaction:
        g = pd.get_dummies(universe["food_group"], prefix="g")
        f = universe["proc_fams"].str.get_dummies("|")
        for gc in g.columns:
            for fc in f.columns:
                feats[f"{gc}x{fc}"] = g[gc] * f[fc]
    lr = LogisticRegression(max_iter=2000, C=1.0)
    lr.fit(feats.to_numpy(float), universe["obs"].to_numpy())
    universe["p"] = lr.predict_proba(feats.to_numpy(float))[:, 1]
    obs = universe[universe["obs"]]
    p_of = {(i, s): p for i, s, p in zip(obs["ingredient"], obs["proc_sig"], obs["p"], strict=True)}
    return {"p_of": p_of, "universe": len(universe), "observed": int(universe["obs"].sum()),
            "p_min": float(obs["p"].min()), "p_median": float(obs["p"].median()),
            "p_max": float(obs["p"].max()), "clipped_share": float((obs["p"] < 0.05).mean())}


# ------------------------------------------------------------------ bootstrap (card N)
def grouped_boot(err: np.ndarray, groups: np.ndarray, n_boot=2000, seed=0, weights=None):
    rng = np.random.default_rng(seed)
    uniq, inv = np.unique(groups, return_inverse=True)
    w = np.ones_like(err) if weights is None else weights
    s = np.bincount(inv, weights=err * w, minlength=len(uniq))
    c = np.bincount(inv, weights=w, minlength=len(uniq))
    idx = rng.integers(0, len(uniq), (n_boot, len(uniq)))
    stats = s[idx].sum(1) / c[idx].sum(1)
    return float((s.sum() / c.sum())), float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))
