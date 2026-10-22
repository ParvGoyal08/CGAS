# DEL-2 pre-registration — sparsity-aware completion + cold-split benchmark

**Experiments:** SX-13-01 (baselines D0–D6), SX-13-03 (D7 evidence-aware completion
vs tabular), SX-13-04 (MNAR propensity-corrected evaluation) · **Gates:** G15-2, G15-3,
G15-6, G15-7, G15-9, G14-4…12 · **Owner:** Parv · **Reviewer:** Kush
**Frozen:** 2026-10-08, before any retention value distribution was inspected. The
SHA-256 of this file is recorded in `registry/preregistration.csv`. Any later edit is
a new version, with the reason stated.

**What was seen before freezing (disclosure):** R6 structure only — 7 columns,
7,018 rows, 270 retention codes, 13 food groups, 26 nutrients; the data dictionary
and the documentation PDF; the first 3 data rows (values 100); and the 24-row
defect (code 5005, no factor value). No histogram, mean, or per-group value of
`Retn_Factor` was computed.

---

## A. Claim (falsifiable)
1. **H2:** on held-out (food, process) pairs and held-out foods, a model with
   process information has lower censor-aware MAE than the same model without
   it (food identity + nutrient only).
2. **D7:** evidence-aware factorisation completion beats the best tabular
   baseline (D5) on pair-holdout without catastrophic harm on ingredient-disjoint
   splits (AM5).

## B. Data support audit
- **USDA R6** (SRC-0001, CC0): 270 retention codes, each one food category × one
  preparation (e.g. `BEEF,GROUND,BRWN,SIMMER,W/DRIPPINGS`); 26 food components; 7,018
  rows; values are integer percent.
- **Documented source properties (retn06.pdf p.1–3):**
  - "reports nutrient retention factors to the nearest 5 percent";
  - "Factors calculated above 100 percent are reported as 100 percent";
  - most factors use **true retention** `%TR = (Nc·Gc)/(Nr·Gr)·100`, some
    **apparent retention** (dry basis); the per-row method is not stated;
  - some factors were **imputed** by USDA ("many" choline factors); which rows is
    not stated.
- **Phenol-Explorer 3.0** (1,253 RFs) is added as a second source if WP K4 obtains
  it. Every analysis is run per source and pooled.
- **Defect:** code 5005 has no factor in 24 rows → `UNKNOWN`, excluded from
  evaluation, counted in the data card.

## C. Evidence status
Tier **E3** (database aggregate), `origin_type = DATABASE_AGGREGATE`. No row is
human-verified by us; G15-H applies only to literature rows, which are not in the
DEL-2 test sets unless verified.

## D. Confound register
1. **Food identity dominates** process effects (Rothwell 2015, cited in the
   proposal) → identity-only comparators are mandatory.
2. **Nutrient class:** water-soluble vitamins vs fat-soluble vs minerals vs alcohol vs choline.
3. **Right-censoring at 100** → metric K.
4. **5-percent rounding:** a ±2.5-point measurement floor. Differences smaller than
   this are not interpretable.
5. **USDA imputation from similar foods/methods** can copy values across codes,
   inflating nearest-neighbour baselines → leakage audit G.
6. **Preparation encoded in free-text abbreviations** (`BRWN`, `SIMMRD`, `W/DRIP`) →
   the parse is itself audited (P).
7. **R6 has no temperatures or times:** every condition is `UNKNOWN` (AM1).

## E. Baselines (frozen; SSOT D-ladder, L18547–18609)

| Rung | Definition |
|---|---|
| D0 | persistence: 100% retained (no loss) |
| D1 | global mean of training cells, per nutrient |
| D2 | per (process, nutrient) training mean; falls back to D1 |
| D3 | hierarchical shrinkage: empirical-Bayes partial pooling of (food group × process) toward D2, per nutrient |
| D4 | nearest evidence: same nutrient + process, most similar training food (food group, then token Jaccard) |
| D5 | LightGBM on categorical features (food group, food tokens, process tokens, process family, nutrient, nutrient class) |
| D6 | TabPFN — **NOT RUN** unless installable on CPU; recorded as not run, not silently dropped |
| D7 | factorisation machine with side information (food group, process family, nutrient class) + a biased-MF comparator over rows = (food, process) × columns = nutrient |

**H2 comparators:** D5-noproc and D7-noproc (identical but without process features).

## F. Splits (frozen; 5 folds × 3 seeds: 20261008, 20261009, 20261010)

| Split | Unit held out | Status |
|---|---|---|
| **pair-holdout** (headline) | whole retention codes (a food × preparation pair, all its nutrients) | run |
| **ingredient-disjoint** (headline) | every code of a parsed food key | run |
| process-disjoint | every code of a parsed process | run, secondary |
| random masked-cell | individual cells | **sanity only, never a headline** |
| study-disjoint | — | **infeasible on R6** (one aggregate source; AM3). Becomes source-held-out (R6 ↔ PE) if PE is acquired |

## G. Leakage audit (before any model)
- Exact-duplicate nutrient vectors across codes (a signature of imputation) → codes
  with identical vectors are grouped into the same fold, and their count is reported.
- Duplicate normalised descriptions → grouped.

## H. Proposed method
D7 (as in E).

## I. Hyperparameter budget
Inner 3-fold CV on training folds only.
- LightGBM: num_leaves ∈ {7, 15, 31}, n_estimators ∈ {200, 500}, learning_rate 0.05.
- FM/MF: rank ∈ {2, 4, 8}, L2 ∈ {1e-3, 1e-2, 1e-1}.

Nothing is tuned on test folds.

## J. Calibration
Split-conformal with absolute residuals on a calibration slice carved from each
training fold. **Report empirical coverage and width at nominal 90%; claim no
nominal validity under these shifts** (v4.0 AH4).

## K. Primary metric
**Censor-aware MAE** on retention percent:
- uncensored truth `y < 100`: error = |ŷ − y|;
- censored truth `y = 100` (true value ≥ 100): error = max(0, 100 − ŷ).

## L. Secondary metrics
RMSE (uncensored cells), Spearman ρ, interval coverage/width, IPS-weighted MAE.

## M. Subgroups
Food group; process family; nutrient class.

## N. Uncertainty
Grouped bootstrap, 2,000 resamples over the held-out unit (code or food), 95% CI.
Model differences use a **paired** grouped bootstrap.

## O. Ablations
Without process features; without food group; without nutrient-class side information (D7).

## P. Oracle upstream
A hand check of the RetnDesc → (food, process tokens) parse on 30 random codes;
parse accuracy is reported.

## Q. Error analysis
The 20 largest residuals per split; censored cells; suspected imputation clusters.

## R. Negative control
Permute process labels within food group. The process model's advantage must
disappear; if it does not, suspect leakage.

## S. Positive control
Add a known synthetic process effect (−20 points for one process on a copy of the
data). The models must recover it.

## T. Reproducibility
Data `SNAP-` hash, code hash, `requirements.lock.txt`, seeds; every run writes
`experiments/DEL2/runs/<run-id>/`.

## U. Success gates
- **H2 supported** iff the paired-bootstrap 95% CI of
  MAE(identity-only) − MAE(with process) is > 0 on **both** pair-holdout and
  ingredient-disjoint (G15-3).
- **D7 promoted** iff the CI of MAE(D5) − MAE(D7) is > 0 on pair-holdout **and**
  D7's ingredient-disjoint MAE is not more than 10% (relative) worse than D5's
  (AM5, G15-9).

## V. Null decision
CI includes 0 → "no evidence that process information helps on R6", reported as such.

## W. Negative decision
Process features hurt → reported. B6 is then dropped from DEL-5.

## X. Data-limited decision
A split with fewer than 30 held-out groups → "underpowered"; no claim.

## Y. External validity
US data, compiled 1975–2007; preparation categories only, no condition
resolution. Results do **not** imply condition-independent process effects (AM1).

## Z. Downstream
DEL-4's `model-estimated` evidence class may use the best D-rung only if U passes.
Otherwise DEL-5 runs without B6.

---

### SX-13-04 — propensity / MNAR (same freeze)
- **Universe:** every (parsed food key × parsed process) combination among R6's
  foods and processes. Observed pairs = the 270 codes.
- **Propensity:** logistic regression P(pair observed | food group, process family),
  plus a second specification adding food-group × process-family interaction (a
  sensitivity check).
- **Weights:** IPS = 1/p for observed test pairs, clipped at p ≥ 0.05. Report
  overlap (min/median propensity) and **weighted beside unweighted** MAE (AM4).
- **Limitation (stated now):** the propensity is a modelling assumption, not known
  truth.
