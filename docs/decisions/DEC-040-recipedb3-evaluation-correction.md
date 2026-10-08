# DEC-040 — RecipeDB3 NER: evaluation correction (2026-10-09)

**Status:** APPROVED by Parv, 9 Oct 2026, in session.

**Evidence:** `research/briefs/RS-08-ner-landscape.md` (card NERRES-03) and `registry/ner_resources.csv` (row NERRES-03). These were verified from the public notebook *outputs* in `github.com/cosylabiiit/RecipeDB3_NER_Research_Paper`, which was created 2026-07-06. Nothing was downloaded or run.

## Recorded findings

The status of each is given in brackets.

| # | Finding | Status |
|---|---|---|
| 1 | The ingredient NER model is `microsoft/deberta-base` (DeBERTa **v1**), with **no CRF** layer. It is not DeBERTa-v3 + CRF | [VERIFIED from the notebook] |
| 2 | The released notebook appears to **select the best model/checkpoint on the test set**, so the reported score may be optimistically biased | [INFERENCE from the notebook code/output; to be confirmed when the run is reproduced] |
| 3 | `SIZE` labels are mapped to `O` before evaluation, so SIZE is never scored | [VERIFIED from the notebook] |
| 4 | No RecipeDB3 paper was found. The repository has **no licence** (GitHub API: `license = null`; no LICENSE file) | [VERIFIED] |
| 5 | The notebooks load data files whose names differ from the repo CSVs, so whether they are the same data is unverified | [OPEN QUESTION] |
| 6 | The master plan's 5.1% / 13.6% duplicate rates | [OPEN QUESTION — unverified] |

## How the reported numbers are carried

The numbers are kept but never adopted as our baseline. They are recorded as:

```text
RecipeDB3 ingredient NER macro-F1 0.9557; instruction NER micro-F1 0.9258 / macro-F1 0.8698
labels: SOURCE_REPORTED · NOT_INDEPENDENTLY_REPRODUCED · TEST_SELECTION_BIAS_POSSIBLE · SIZE_NOT_SCORED · LICENCE_PERMISSION_REQUIRED
```

The wording rule, used from now on:

> "RecipeDB3 reports X under its released evaluation procedure. We reproduce a matched version and separately report a leakage-safe, dev-selected evaluation."

Never write: "RecipeDB3 achieved X, therefore X is our baseline."

## Consequences

| Area | Consequence |
|---|---|
| Use of artefacts | No copying, training on, or releasing anything derived from the RecipeDB3 artefacts until Prof. Bagler / CoSyLab give **written permission**. This is requested in the professor email (H1) |
| Reproduction protocol | `experiments/B08/recipedb3_repro/card.md` (frozen): matched-to-source view A, corrected/full view B, Δ_test-selection, and a SIZE ablation |
| Master plan v4.0, L392 and L701 | They describe the result without these caveats and propose "DeBERTa/RoBERTa ± CRF". Change request **CR-0003** in `registry/change_requests.md`. The plan itself is not edited |
| Research questions | Two new questions are registered as RS-08-NEW-01/02: **RQ_NER-EVAL** — how much does test-set model selection inflate reported recipe-NER performance? **RQ_SIZE** — how much does omitting a hard attribute (SIZE) change aggregate NER performance? |
