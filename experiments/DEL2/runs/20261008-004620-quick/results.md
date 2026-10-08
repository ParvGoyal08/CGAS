# DEL-2 results — run `20261008-004620-quick`

Card sha `da8430244208f88c…` (unchanged since freeze; `gate.py` G-PREREG). Cells 6,994; censored at 100: 37.5%. Seeds 20261008. Primary metric: censor-aware MAE (retention points); 95% CIs from a 2,000-resample grouped bootstrap.

**Seed rule (DEC-032):** the card does not say how to combine seeds; a gate passes only if it passes in every seed.

## Gate verdicts (card §U–§X)

Held-out groups — pair 176, ingredient 19 (card §X: < 30 → underpowered, no claim).

| Gate | Verdict |
|---|---|
| H2 — process information helps (D5 family) | **UNDERPOWERED** |
| H2 — process information helps (D7 family) | **UNDERPOWERED** |
| D7 promotion (AM5 / G15-9) | **UNDERPOWERED → NOT PROMOTED (card §X: the ingredient harm check cannot be established)** |
| Negative control (permuted processes) | **NOT RUN in this run** |
| Positive control (−20 on boil) | NOT RUN |

## Split: pair

| Model | MAE seed 20261008 [95% CI] | IPS-MAE (seed 1) |
|---|---|---|
| D0 | 12.16 [10.53, 13.76] | 14.18 |
| D1 | 9.32 [8.65, 10.06] | 10.04 |
| D2 | 6.35 [5.70, 7.06] | 6.66 |
| D3 | 5.90 [5.21, 6.61] | 6.51 |
| D4 | 5.94 [5.06, 6.85] | 6.84 |
| D5 | 5.23 [4.72, 5.74] | 5.72 |
| D5-noproc | 6.81 [6.22, 7.42] | 7.01 |
| D7 | 4.96 [4.50, 5.42] | 5.32 |
| D7-noproc | 6.68 [5.99, 7.39] | 6.79 |
| MF-biased | nan [nan, nan] | nan |

| Paired difference (positive = right model better) | seed 20261008 |
|---|---|
| D5-noproc minus D5 (H2) | 1.58 [1.06, 2.16] |
| D7-noproc minus D7 (H2) | 1.72 [1.15, 2.30] |
| D5 minus D7 (D7 promotion) | 0.27 [-0.11, 0.62] |
| D4 minus D5 | 0.71 [0.08, 1.35] |

Empirical split-conformal (nominal 90%; **no validity claim under shift**, AH4), seed 20261008: D5 coverage 92.6% width 27.4; D7 coverage 93.3% width 28.3

Held-out groups: 176

## Split: ingredient

| Model | MAE seed 20261008 [95% CI] | IPS-MAE (seed 1) |
|---|---|---|
| D0 | 12.16 [7.70, 15.95] | 14.18 |
| D1 | 10.00 [8.33, 11.43] | 10.81 |
| D2 | 8.02 [6.75, 9.17] | 8.93 |
| D3 | 7.95 [6.62, 9.17] | 8.90 |
| D4 | 7.65 [6.30, 9.11] | 8.63 |
| D5 | 8.34 [6.21, 9.99] | 9.57 |
| D5-noproc | 9.49 [6.98, 11.52] | 10.67 |
| D7 | 9.15 [7.54, 10.52] | 10.26 |
| D7-noproc | 9.92 [7.98, 11.61] | 10.99 |
| MF-biased | nan [nan, nan] | nan |

| Paired difference (positive = right model better) | seed 20261008 |
|---|---|
| D5-noproc minus D5 (H2) | 1.15 [0.30, 1.84] |
| D7-noproc minus D7 (H2) | 0.77 [-0.01, 1.36] |
| D5 minus D7 (D7 promotion) | -0.81 [-1.63, -0.29] |
| D4 minus D5 | -0.70 [-1.81, 0.68] |

Empirical split-conformal (nominal 90%; **no validity claim under shift**, AH4), seed 20261008: D5 coverage 83.4% width 33.4; D7 coverage 86.0% width 32.6

Held-out groups: 19

## Split: process

| Model | MAE seed 20261008 [95% CI] | IPS-MAE (seed 1) |
|---|---|---|
| D0 | 12.16 [5.34, 14.38] | — |
| D1 | 10.39 [9.17, 12.31] | — |
| D2 | 10.39 [9.17, 12.31] | — |
| D3 | 10.39 [9.17, 12.31] | — |
| D4 | 10.39 [9.17, 12.31] | — |
| D5 | 8.47 [5.27, 8.98] | — |
| D5-noproc | 10.45 [5.26, 11.39] | — |
| D7 | 8.65 [5.26, 9.18] | — |
| D7-noproc | 10.35 [4.65, 11.38] | — |
| MF-biased | nan [nan, nan] | — |

| Paired difference (positive = right model better) | seed 20261008 |
|---|---|
| D5-noproc minus D5 (H2) | 1.99 [-0.47, 2.48] |
| D7-noproc minus D7 (H2) | 1.70 [-1.91, 2.36] |
| D5 minus D7 (D7 promotion) | -0.19 [-1.03, 0.20] |
| D4 minus D5 | 1.92 [1.16, 5.65] |

Empirical split-conformal (nominal 90%; **no validity claim under shift**, AH4), seed 20261008: D5 coverage 91.0% width 33.2; D7 coverage 91.9% width 37.1

Held-out groups: 31

## Split: random

| Model | MAE seed 20261008 [95% CI] | IPS-MAE (seed 1) |
|---|---|---|
| D0 | 12.16 [11.84, 12.49] | — |
| D1 | 9.23 [9.04, 9.42] | — |
| D2 | 6.12 [5.95, 6.29] | — |
| D3 | 5.49 [5.32, 5.66] | — |
| D4 | 5.08 [4.89, 5.26] | — |
| D5 | 4.40 [4.29, 4.51] | — |
| D5-noproc | 5.53 [5.39, 5.66] | — |
| D7 | 3.70 [3.59, 3.80] | — |
| D7-noproc | 4.61 [4.47, 4.73] | — |
| MF-biased | nan [nan, nan] | — |

| Paired difference (positive = right model better) | seed 20261008 |
|---|---|
| D5-noproc minus D5 (H2) | 1.13 [1.03, 1.22] |
| D7-noproc minus D7 (H2) | 0.91 [0.81, 1.02] |
| D5 minus D7 (D7 promotion) | 0.70 [0.62, 0.79] |
| D4 minus D5 | 0.68 [0.52, 0.84] |

Empirical split-conformal (nominal 90%; **no validity claim under shift**, AH4), seed 20261008: D5 coverage 91.2% width 20.9; D7 coverage 91.9% width 18.9

Held-out groups: 6994

## SX-13-04 propensity (overlap)

Universe 1,692 food × process pairs, observed 172; propensity min 0.014, median 0.160; clipped at 0.05: 4.1%. The propensity is a modelling assumption, not known truth (card).

## Limits (card §Y)

US data compiled 1975–2007; preparation categories only, no temperatures. Results do **not** imply condition-independent process effects (AM1). 143 of 270 codes sit in USDA duplicate-imputation clusters, which are grouped before splitting.

