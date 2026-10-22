# B08 — RecipeDB3 NER reproduction card (FROZEN 2026-10-09, before any data access)

**Decisions:** DEC-039 and DEC-040.

**Status:** the data and artefacts need **written permission** from Prof. Bagler / CoSyLab (H1 email item 2). Nothing is downloaded or run before that permission arrives.

**Scorer:** the common P14 scorer, `src/culinarystate/ner/scorer.py` (exact and overlap span P/R/F1; per-label; micro and macro).

## Claim being tested

RecipeDB3 reports ingredient NER macro-F1 0.9557 and instruction NER micro-F1 0.9258 / macro-F1 0.8698 (SOURCE_REPORTED, DEC-040). We test:

- **H-A (matched):** under the source protocol, our rerun lands within ±0.01 F1 of the reported numbers. A miss of more than 0.01 is reported as "not reproduced", together with the observed gap.
- **H-B (corrected):** RQ_NER-EVAL. With selection on dev only, the score drops by Δ_test-selection ≥ 0. We estimate the size of the drop and do not assume one.
- **H-C (SIZE):** RQ_SIZE. Restoring SIZE changes the aggregate macro-F1 by Δ_SIZE. We estimate it and report its sign and size.

## Splits and leakage

1. Rebuild the source split exactly (`test_size=0.2, random_state=42`, as in the notebook) for view A.
2. For view B, carve a **dev split from train only** (15% of train, seed 20261009).
3. Run the duplicate/near-duplicate audit (`leakage_audit`: exact normalised match and word 5-gram Jaccard ≥ 0.8) across train/dev/test. Report every rate, and run view B both on the source split and on a **duplicate-safe split**. Families of near-duplicate items are grouped together, then split 70/15/15 with seed 20261009.
4. **The test split is touched once per view per seed**, after selection is final. Every evaluation call is logged, with a hash of the predictions.

## Views

| View | Model selection | Labels scored | Purpose |
|---|---|---|---|
| **A: matched-to-source** | as released: best checkpoint/model picked **on test** | the source label set with SIZE → O | comparison with the reported numbers only |
| **B: corrected/full** | checkpoint, epochs and hyperparameters picked **on dev only** | FOOD, QUANTITY, UNIT, SIZE, FORM, STATE/QUALITY, plus PROCESS/ACTION where annotated | our reported numbers |

- **Δ_test-selection** = Score(source-style selection on test) − Score(dev-only selection), on the same split and seed. It is reported as an **evaluation-bias analysis**, not as a criticism of the original work.
- **SIZE ablation (view B):** the same predictions scored with SIZE and with SIZE → O. The difference is Δ_SIZE.

## Models

These are the models used in the notebooks; nothing is substituted:

| Task | Model |
|---|---|
| Ingredient NER | `microsoft/deberta-base` (v1), token classification, no CRF |
| Instruction NER | the blank spaCy pipeline from the notebook |

Hyperparameters are copied from the notebook. View B searches only the grid the notebook already uses, so nothing extra can be tuned.

## Reported metrics, for every view and seed

- exact-span P/R/F1 (micro);
- macro-F1;
- per-label support and F1;
- relaxed (overlap) span F1;
- results on the source split and on the duplicate-safe split;
- calibration (ECE over token probabilities, where the model exposes them);
- hardware (CPU/GPU), runtime and peak memory;
- **3 seeds** (20261009, 20261010, 20261011), with 95% CIs from a document-level bootstrap (2,000 resamples).

## Downstream

The research target is semantic parsing plus state reconstruction, not NER alone. Every NER run also reports, where labels exist:

- entity linking;
- quantity/attribute correctness;
- the oracle-span → state-graph gap.

## Decision rules

| Outcome | Wording |
|---|---|
| H-A passes | "matched reproduction within 0.01" |
| H-A fails | "not reproduced under the matched protocol (gap = …)". Nothing is tuned until it matches |
| H-B, H-C | estimates with CIs; no pass/fail |

None of these numbers becomes "our baseline". Baselines are the view-B, dev-selected, duplicate-safe numbers.
