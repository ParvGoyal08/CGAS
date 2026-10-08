# T07 pre-registration — Kinouchi et al. 2008 copy–mutate reproduction (bounded)

**Status: FROZEN (2026-10-09).** Frozen by Parv's instruction in session; executed by Claude after the missing fields were added. No run had been made. The hash and commit are in `FREEZE.md`. Freezing means:

1. Edit any choice below.
2. Change the status to FROZEN, with name and date.
3. Run `shasum -a 256 experiments/B15/kinouchi_v0/prereg.md` and add the hash to `registry/preregistration.csv`.

The simulator is `src/culinarystate/evolution/kinouchi.py`. Its tests check invariants only, on tiny parameters.

**Sources:** the card `research/briefs/L13E-kinouchi2008-card.md`, sections 5–7 and 10. The paper states no tolerances. The preprint resolves none of the ambiguities and conflicts with the published version on A14, A15 and A27 (DEC-037). The **published version is the reference** throughout.

## Hypothesis (exact)

- **H1:** our reimplementation of the published copy–mutate model, with the primary choices below, produces a mean rank–frequency curve f(r) over 5 seeds that lies within 0.2 decade of the paper's published eq. (1) for ≥ 90% of ranks r ∈ [1, 500] (AC-1).
- **H2:** 1 − F_Total(t) first rises and then decays as a power law with γ_sim ∈ [0.05, 0.2] (AC-2).

H1 and H2 together are the reproduction claim. AC-3 and AC-4 are supporting, and AC-5 is a correctness check.

## Source and version

| Copy | Record |
|---|---|
| Published | Kinouchi et al., New J. Phys. 10 (2008) 073020, DOI 10.1088/1367-2630/10/7/073020 (SNAP-L13E-0001, sha256 98db4d2b…afcc). **The reference version** |
| Author preprint | arXiv:0802.4393v1 (SNAP-L13E-0002, sha256 885e618f…29d2). Used only for the comparison in card §10 |

The card is `research/briefs/L13E-kinouchi2008-card.md`. Its transcribed numbers are on the human spot-check list (§9).

## Normalisation

- **Simulation:** ingredients are integer ids, so no name normalisation is needed.
- **No empirical recomputation:** the paper's cookbook data are not released (A23). Neither the paper's Figs. 1–2 nor the A1 corpus are refitted inside this experiment.

## Rank–frequency statistic

As in A12:

- f(r) = (number of recipes containing the rank-r ingredient) / (total recipes R, founders included);
- ingredients that are never used are excluded;
- ranks are ordered by f, descending; ties broken by ingredient id.

## Parameters (Fig. 3)

- (T, K, L, M, R0) = (1200, 11, 4, 3, 20).
- Fitness ~ U[0,1].
- 5 seeds: `20261008 + s`, s = 0…4 (A22: the paper reports none).

## Choices for each open ambiguity

| Id | Question | Primary choice (`Config` default) | Sensitivity run |
|---|---|---|---|
| A1/A2 | How are the initial recipes and pool built? (the paper contradicts itself: K·R0 = 220 vs M·R0 = 60) | **IC-a**: pool M·R0 = 60; each of the R0 recipes takes K distinct ingredients uniformly from it | **IC-b**: 220 distinct founders form the pool; the pool grows once M·R(t) > 220 |
| A3 | Is T the final recipe count or the number of steps? | stop when R = T (1,180 steps) | T steps (1,220 recipes) |
| A4 | L loci with or without replacement? | independent draw per repeat ("repeated L times") | without replacement |
| A5 | Where does j come from? | uniform over the whole pool, including never-used ingredients | — |
| A6 | j already in the daughter? | no replacement (recipes stay sets; matches the published counting rule) | — |
| A7 | Fitness of new pool ingredients? | U[0,1] | — |
| A8 | When does the pool grow, and by how much? | after the daughter is added: \|P\| = M·R(t+1), i.e. exactly 3 per step | — |
| A9 | How is the mother chosen? | uniform over all existing recipes, including founders | — |
| A10 | Do the L comparisons act sequentially? | yes, on the progressively mutated copy | — |
| A11 | Fixed K | no recipe-size comparison is attempted | — |
| A12 | How is f(r) computed? | share of **all** recipes (including founders) containing the rank-r ingredient; never-used ingredients excluded | — |
| A13 | How are the 5 runs averaged? | rank-wise mean over ranks present in all 5 seeds; per-seed curves also reported | — |
| A14 | Which eq. (1) is the reference? | **published**: f = C/(a + r)^β · e^(−r/r_c), with C = 8.7, a = 6.4, β = 1.31, r_c = 800 | — |
| A17 | Fig. 4 parameters | same as Fig. 3, 5 seeds; γ fitted over the decaying segment | — |
| A18 | Fig. 5 | seed 0 only; never-used ingredients excluded | — |
| A21 | What does "without fitness selection" mean? | `selection="always"` (j always replaces i) | — |
| A15, A27 | α and α = 1 + 1/β | **not used**: there is no empirical data to recompute, and the relation is inconsistent in the published numbers | — |

## Fitting method

| Item | Method |
|---|---|
| AC-1 | **no fit**: the simulated f(r) is compared with eq. (1) at the published parameters |
| AC-2 | OLS of log(1 − F_Total) on log t, over the decaying segment (from argmax to the end), per seed and for the seed mean |
| Heavy tails | discrete Clauset–Shalizi–Newman (CSN) MLE with KS-selected x_min, applied to the **counts** (recipes per ingredient), using the B15 code (`src/culinarystate/evolution/csn.py`) |

## Candidate heavy-tail alternatives (descriptive, not pass/fail)

On the seed-0 primary run's ingredient counts, fit a power law, lognormal, truncated power law and exponential. Compare them with a Vuong test (power law vs lognormal and vs exponential) and a χ²₁ likelihood-ratio test (power law vs truncated power law), as in DEC-024.

## Goodness of fit

| Criterion | Measure |
|---|---|
| AC-1 | share of ranks inside the ±0.2-decade band |
| Heavy-tail fits | KS distance, plus a semi-parametric bootstrap p-value (1,000 resamples; p < 0.1 rejects the power law) |
| AC-2 | R² of the OLS line, reported alongside γ_sim |

## Null models (descriptive)

| Null | Definition |
|---|---|
| N1, no selection | `selection="always"`: j always replaces i. This is also the AC-4 ablation (A21) |
| N2, size-controlled uniform | T recipes of exactly K ingredients, drawn uniformly without replacement from the primary run's final pool. This is A2's Q2(a) control applied to the model |

f(r) is reported for both nulls, next to the model.

## Planned figures and tables

| ID | Content |
|---|---|
| F1 | f(r) log–log: seed mean ± min/max envelope; published eq. (1); N1; N2 |
| F2 | 1 − F_Total(t) log–log, per seed, with the fitted γ line |
| F3 | ingredient fitness vs rank (seed 0), founders highlighted |
| F4 | founder share of ranks 1…K·R0, with vs without selection |
| T1 | AC-1…AC-5 verdicts, per IC variant and per A3/A4 variant |
| T2 | the heavy-tail fit table (α, x_min, KS, bootstrap p, Vuong/LR) |

## No post-result changes

Thresholds, ranges, seeds, variants and figures are fixed by this file. After the first run:

- nothing here is changed;
- any extra analysis is labelled **EXPLORATORY** in a separate file;
- a failure is reported as a failure.

## Acceptance criteria

These are frozen together with the choices above. Full text in the card, §7.3.

| Criterion | Pass condition |
|---|---|
| AC-1 | ≥ 90% of ranks r ∈ [1, 500] within 0.2 decade of the published eq. (1) |
| AC-2 | 1 − F_Total(t) rises then decays; γ_sim ∈ [0.05, 0.2] |
| AC-3 | in ≥ 4 of 5 seeds: mean fitness > 0.5; a founder with f < 0.2 at r ≤ K·R0; an ingredient with f > 0.8 at r > 500 |
| AC-4 | founder share of ranks 1…K·R0 is higher without selection than with it |
| AC-5 | invariants exact (already unit-tested) |

**Overall:** "Reproduced (bounded)" only if AC-1, AC-2 and AC-5 pass under the primary choices. Every sensitivity run is reported whatever its outcome. A failure is reported as a failure, never tuned away. The paper defines no founder-effect statistic, so ours is descriptive only.

**Not comparable:** B15's α = 1.63 (CSN discrete MLE on the A1 corpus) and the paper's α ≅ 1.73 (a line fit over an unstated range).

**Frozen by:** Parv (session instruction 2026-10-09). The sha256 and git commit are in `FREEZE.md`.
