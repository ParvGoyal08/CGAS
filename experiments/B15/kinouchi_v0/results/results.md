# T07 Kinouchi reproduction — results

Pre-registration sha256 `3602f58dc6d1e672…` (frozen; checked before run). Seeds [20261008, 20261009, 20261010, 20261011, 20261012].

**Overall (pre-registered rule: AC-1, AC-2, AC-5 under primary): NOT REPRODUCED**

| Variant | AC-1 share ≤0.2 dec (pass ≥0.9) | AC-2 γ (pass 0.05–0.2) / rises-then-decays | AC-3 (≥4/5 seeds) | AC-5 |
|---|---|---|---|---|
| primary | 1.000 PASS | — / False FAIL | 5/5 PASS | PASS |
| IC-b | 0.182 FAIL | — / False FAIL | 5/5 PASS | PASS |
| A3_T_steps | 1.000 PASS | — / False FAIL | 5/5 PASS | PASS |
| A4_without_replacement | 0.998 PASS | — / False FAIL | 5/5 PASS | PASS |
| N1_no_selection | 0.388 FAIL | 0.003 / True FAIL | 2/5 FAIL | PASS |

**AC-4** founder share of ranks 1…K·R0: with selection 0.262, without 0.265 → PASS

**T2 heavy tail (seed 0, primary; descriptive):** xmin 2, α 1.696, KS 0.031, bootstrap p 0.077; power_law_vs_exponential: power_law; power_law_vs_lognormal: lognormal; power_law_vs_truncated_power_law: truncated_power_law

Figures: F1_rank_frequency.png, F2_fitness_gap.png, F3_fitness_vs_rank.png, F4_founder_share.png.

No threshold, range, seed or variant was changed after the run (prereg 'No post-result changes').

## Reading the result

The labels below are VERIFIED / INFERENCE / OPEN, as in DEC-041.

- **[VERIFIED] Rank–frequency curve reproduced.** Under the primary initial condition, the 5-seed mean f(r) lies within 0.2 decade of the published eq. (1) for 100% of ranks 1–500 (AC-1). Selection matters: without it (N1), only 38.8% of ranks are within the band. The uniform null (N2) is flat.
- **[VERIFIED] Rank–frequency depends on the initial condition.** IC-b, with 220 distinct founders, fails AC-1 (18.2%). So the reading of ambiguity A1 decides whether the curve reproduces.
- **[VERIFIED] Fitness-gap shape not reproduced (AC-2).** 1 − F_Total(t) decreases from the first step in the seed mean; there is no initial rise. By the pre-registered rule, the overall verdict is **NOT REPRODUCED**.
- **[VERIFIED] Founder effect not demonstrated (AC-4).** AC-4 passes by the frozen rule (0.265 > 0.262), but the difference is negligible and does not count as evidence of a founder effect.
- **[EXPLORATORY] Decay exponent.** The decay over the full series has γ ≈ 0.089, near the paper's 0.1. See `EXPLORATORY_gamma_full_series.json`.
- **[INFERENCE / OPEN] Where the rise may come from.** The published rise may occur while the founder recipes are built (paper axis from t = 1; our model from t = 21). This needs the authors, or a new pre-registered variant. It must not be added post hoc.
- **[VERIFIED, descriptive] Heavy tail.** The model's counts are heavy-tailed but not a pure power law (bootstrap p = 0.077 < 0.1; lognormal and truncated power law favoured). This is qualitatively like our A1 corpus result (DEC-024).
