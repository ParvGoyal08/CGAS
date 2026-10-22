# DEL-2 results — run `20261008-004800`

Card sha `da8430244208f88c…` (unchanged since freeze; `gate.py` G-PREREG). Cells 6,994; censored at 100: 37.5%. Seeds 20261008, 20261009, 20261010. Primary metric: censor-aware MAE (retention points); 95% CIs from a 2,000-resample grouped bootstrap.

**Seed rule (DEC-032):** the card does not say how to combine seeds; a gate passes only if it passes in every seed.

## Gate verdicts (card §U–§X)

Held-out groups — pair 176, ingredient 19 (card §X: < 30 → underpowered, no claim).

| Gate | Verdict |
|---|---|
| H2 — process information helps (D5 family) | **UNDERPOWERED** |
| H2 — process information helps (D7 family) | **UNDERPOWERED** |
| D7 promotion (AM5 / G15-9) | **UNDERPOWERED → NOT PROMOTED (card §X: the ingredient harm check cannot be established)** |
| Negative control (permuted processes) | **PASS (advantage gone)** |
| Positive control (−20 on boil) | recovered -19.7 of −20 (98%); spillover on other cells -0.00 |

## Split: pair

| Model | MAE seed 20261008 [95% CI] | MAE seed 20261009 [95% CI] | MAE seed 20261010 [95% CI] | IPS-MAE (seed 1) |
|---|---|---|---|---|
| D0 | 12.16 [10.53, 13.76] | 12.16 [10.54, 13.77] | 12.16 [10.45, 13.84] | 14.18 |
| D1 | 9.32 [8.65, 10.06] | 9.29 [8.63, 9.99] | 9.28 [8.55, 9.99] | 10.04 |
| D2 | 6.35 [5.70, 7.06] | 6.25 [5.66, 6.87] | 6.33 [5.70, 6.98] | 6.66 |
| D3 | 5.90 [5.21, 6.61] | 5.82 [5.19, 6.48] | 5.81 [5.12, 6.50] | 6.51 |
| D4 | 5.94 [5.06, 6.85] | 5.74 [4.93, 6.62] | 5.95 [5.06, 6.83] | 6.84 |
| D5 | 4.21 [3.76, 4.67] | 4.33 [3.84, 4.84] | 4.41 [3.84, 5.00] | 4.62 |
| D5-noproc | 6.62 [5.97, 7.31] | 6.28 [5.68, 6.90] | 6.48 [5.80, 7.14] | 6.74 |
| D7 | 5.01 [4.50, 5.55] | 5.01 [4.48, 5.54] | 5.34 [4.78, 5.91] | 5.46 |
| D7-noproc | 6.20 [5.50, 6.94] | 6.24 [5.65, 6.87] | 6.40 [5.76, 7.04] | 6.13 |
| MF-biased | 10.44 [9.68, 11.19] | 10.40 [9.67, 11.15] | 10.39 [9.59, 11.15] | 11.48 |

| Paired difference (positive = right model better) | seed 20261008 | seed 20261009 | seed 20261010 |
|---|---|---|---|
| D5-noproc minus D5 (H2) | 2.40 [1.79, 3.07] | 1.95 [1.34, 2.58] | 2.07 [1.41, 2.77] |
| D7-noproc minus D7 (H2) | 1.19 [0.42, 1.97] | 1.23 [0.69, 1.81] | 1.06 [0.43, 1.76] |
| D5 minus D7 (D7 promotion) | -0.79 [-1.04, -0.54] | -0.68 [-0.99, -0.37] | -0.93 [-1.26, -0.65] |
| D4 minus D5 | 1.73 [1.08, 2.38] | 1.40 [0.86, 1.91] | 1.54 [0.99, 2.06] |

Empirical split-conformal (nominal 90%; **no validity claim under shift**, AH4), seed 20261008: D5 coverage 92.9% width 24.6; D7 coverage 93.4% width 27.5

Held-out groups: 176, 176, 176

## Split: ingredient

| Model | MAE seed 20261008 [95% CI] | MAE seed 20261009 [95% CI] | MAE seed 20261010 [95% CI] | IPS-MAE (seed 1) |
|---|---|---|---|---|
| D0 | 12.16 [7.70, 15.95] | 12.16 [7.62, 15.91] | 12.16 [7.61, 15.84] | 14.18 |
| D1 | 10.00 [8.33, 11.43] | 9.71 [8.03, 11.10] | 10.43 [7.75, 12.47] | 10.81 |
| D2 | 8.02 [6.75, 9.17] | 7.48 [6.44, 8.81] | 9.02 [6.39, 11.13] | 8.93 |
| D3 | 7.95 [6.62, 9.17] | 7.37 [6.20, 8.82] | 8.90 [6.19, 11.09] | 8.90 |
| D4 | 7.65 [6.30, 9.11] | 7.15 [5.91, 8.86] | 8.76 [5.91, 11.08] | 8.63 |
| D5 | 8.16 [5.83, 10.00] | 7.46 [5.30, 9.33] | 8.36 [5.44, 10.79] | 9.37 |
| D5-noproc | 9.34 [6.73, 11.42] | 8.72 [6.16, 10.95] | 9.30 [6.34, 11.75] | 10.53 |
| D7 | 8.77 [7.52, 9.92] | 8.64 [7.24, 9.89] | 9.11 [7.33, 10.54] | 9.66 |
| D7-noproc | 9.98 [8.01, 11.59] | 9.73 [8.20, 11.29] | 10.40 [7.60, 12.67] | 11.00 |
| MF-biased | 10.85 [8.81, 12.57] | 10.53 [8.53, 12.20] | 11.29 [8.40, 13.54] | 11.96 |

| Paired difference (positive = right model better) | seed 20261008 | seed 20261009 | seed 20261010 |
|---|---|---|---|
| D5-noproc minus D5 (H2) | 1.18 [0.29, 2.01] | 1.26 [0.59, 1.95] | 0.94 [0.40, 1.53] |
| D7-noproc minus D7 (H2) | 1.21 [-0.08, 2.21] | 1.09 [0.44, 1.92] | 1.29 [0.08, 2.25] |
| D5 minus D7 (D7 promotion) | -0.61 [-1.89, 0.42] | -1.18 [-2.10, -0.30] | -0.76 [-2.28, 0.33] |
| D4 minus D5 | -0.51 [-1.83, 1.04] | -0.31 [-1.91, 1.46] | 0.40 [0.02, 0.88] |

Empirical split-conformal (nominal 90%; **no validity claim under shift**, AH4), seed 20261008: D5 coverage 83.9% width 33.3; D7 coverage 86.3% width 32.3

Held-out groups: 19, 19, 19

## Split: process

| Model | MAE seed 20261008 [95% CI] | MAE seed 20261009 [95% CI] | MAE seed 20261010 [95% CI] | IPS-MAE (seed 1) |
|---|---|---|---|---|
| D0 | 12.16 [5.34, 14.38] | 12.16 [5.35, 14.39] | 12.16 [5.44, 14.56] | — |
| D1 | 10.39 [9.17, 12.31] | 10.18 [9.03, 11.75] | 10.05 [8.59, 11.33] | — |
| D2 | 10.39 [9.17, 12.31] | 10.18 [9.03, 11.75] | 10.05 [8.59, 11.33] | — |
| D3 | 10.39 [9.17, 12.31] | 10.18 [9.03, 11.75] | 10.05 [8.59, 11.33] | — |
| D4 | 10.39 [9.17, 12.31] | 10.18 [9.03, 11.75] | 10.05 [8.59, 11.33] | — |
| D5 | 8.20 [4.43, 8.80] | 8.98 [4.32, 9.80] | 8.23 [4.29, 9.11] | — |
| D5-noproc | 10.30 [4.26, 11.40] | 10.48 [4.84, 11.55] | 8.14 [4.33, 8.83] | — |
| D7 | 8.25 [5.21, 8.72] | 9.56 [5.77, 10.20] | 8.74 [4.87, 9.35] | — |
| D7-noproc | 10.17 [4.28, 11.23] | 10.41 [4.51, 11.51] | 7.96 [4.29, 8.71] | — |
| MF-biased | nan [nan, nan] | 10.87 [9.95, 12.16] | nan [nan, nan] | — |

| Paired difference (positive = right model better) | seed 20261008 | seed 20261009 | seed 20261010 |
|---|---|---|---|
| D5-noproc minus D5 (H2) | 2.10 [-0.86, 2.66] | 1.50 [-0.41, 1.80] | -0.08 [-0.85, 1.28] |
| D7-noproc minus D7 (H2) | 1.93 [-1.73, 2.59] | 0.85 [-2.47, 1.40] | -0.78 [-1.39, 0.52] |
| D5 minus D7 (D7 promotion) | -0.05 [-1.63, 0.33] | -0.58 [-2.08, -0.33] | -0.51 [-2.16, -0.09] |
| D4 minus D5 | 2.19 [1.33, 6.30] | 1.20 [0.19, 5.56] | 1.82 [0.82, 5.74] |

Empirical split-conformal (nominal 90%; **no validity claim under shift**, AH4), seed 20261008: D5 coverage 88.6% width 27.6; D7 coverage 93.2% width 36.8

Held-out groups: 31, 31, 31

## Split: random

| Model | MAE seed 20261008 [95% CI] | MAE seed 20261009 [95% CI] | MAE seed 20261010 [95% CI] | IPS-MAE (seed 1) |
|---|---|---|---|---|
| D0 | 12.16 [11.84, 12.49] | 12.16 [11.83, 12.49] | 12.16 [11.85, 12.48] | — |
| D1 | 9.23 [9.04, 9.42] | 9.23 [9.05, 9.42] | 9.23 [9.04, 9.41] | — |
| D2 | 6.12 [5.95, 6.29] | 6.10 [5.94, 6.27] | 6.09 [5.93, 6.27] | — |
| D3 | 5.49 [5.32, 5.66] | 5.46 [5.30, 5.62] | 5.46 [5.30, 5.62] | — |
| D4 | 5.08 [4.89, 5.26] | 5.11 [4.92, 5.30] | 5.00 [4.83, 5.19] | — |
| D5 | 2.85 [2.76, 2.95] | 2.91 [2.81, 3.02] | 2.88 [2.79, 2.97] | — |
| D5-noproc | 4.33 [4.20, 4.46] | 4.34 [4.22, 4.47] | 4.38 [4.25, 4.51] | — |
| D7 | 2.97 [2.88, 3.07] | 2.98 [2.89, 3.07] | 2.99 [2.90, 3.08] | — |
| D7-noproc | 4.13 [4.00, 4.26] | 4.16 [4.04, 4.29] | 4.15 [4.02, 4.28] | — |
| MF-biased | 3.06 [2.94, 3.17] | 3.07 [2.95, 3.19] | 3.09 [2.98, 3.21] | — |

| Paired difference (positive = right model better) | seed 20261008 | seed 20261009 | seed 20261010 |
|---|---|---|---|
| D5-noproc minus D5 (H2) | 1.48 [1.38, 1.58] | 1.43 [1.32, 1.53] | 1.50 [1.40, 1.61] |
| D7-noproc minus D7 (H2) | 1.16 [1.06, 1.26] | 1.18 [1.08, 1.28] | 1.16 [1.07, 1.26] |
| D5 minus D7 (D7 promotion) | -0.12 [-0.19, -0.05] | -0.07 [-0.14, -0.00] | -0.11 [-0.18, -0.05] |
| D4 minus D5 | 2.23 [2.07, 2.38] | 2.19 [2.04, 2.36] | 2.12 [1.97, 2.29] |

Empirical split-conformal (nominal 90%; **no validity claim under shift**, AH4), seed 20261008: D5 coverage 91.8% width 16.1; D7 coverage 91.9% width 15.7

Held-out groups: 6994, 6994, 6994

## SX-13-04 propensity (overlap)

Universe 1,692 food × process pairs, observed 172; propensity min 0.014, median 0.160; clipped at 0.05: 4.1%. The propensity is a modelling assumption, not known truth (card).

## Limits (card §Y)

US data compiled 1975–2007; preparation categories only, no temperatures. Results do **not** imply condition-independent process effects (AM1). 143 of 270 codes sit in USDA duplicate-imputation clusters, which are grouped before splitting.

