# NER_RUNBOOK — only the high-value NER work

**The aim** is recipe semantic parsing plus state reconstruction. NER is one layer of it, not the goal.

**Wording rule (DEC-040):** "RecipeDB3 reports X under its released protocol; we report a matched reproduction and a leakage-safe, dev-selected evaluation." Never "beats CoSyLab / SOTA" without the clean matched test and H6.

| # | Experiment | Status | Command / file |
|---|---|---|---|
| 1 | RecipeDB3 matched (view A) vs corrected (view B); Δ_test-selection; SIZE excluded vs included | card **frozen** | `experiments/B08/recipedb3_repro/card.md`. Needs written permission. **Runner to write** (scorer ready: `src/culinarystate/ner/scorer.py`) |
| 2 | Deterministic baseline: ingredient-parser CRF | H2-C conditional | First verify the licence, record version/hash, check overlap with our gold/test, group recipe families in splits, and check density/portion defaults (must not inject grams). Report as a baseline, never Gold |
| 3 | One encoder (DeBERTa/RoBERTa) trained with dev-only selection | after 1–2 data exist | needs a GPU or long CPU runs (`BLOCKED_COMPUTE` if no GPU) |
| 4 | Schema-flexible challenger: GLiNER v2.1 (Apache-2.0; not v0/v1, which are CC BY-NC) or kNN retrieval NER | after 1 | — |
| 5 | Rules + encoder vs encoder alone, on QUANTITY / TIME / TEMPERATURE / SIZE | after 3 | — |
| 6 | Head/mid/tail retrieval benefit | after 4 | `ner.scorer.frequency_strata` |
| 7 | Oracle spans vs predicted spans → linking → events → state graph | after 3 + D3 gold | `state_graph.agreement`; `ner.scorer.linking_metrics` / `attribute_accuracy` / `relation_f1` |

**Scorer:** exact and overlap span F1 (micro/macro, per label); linking Acc@1 / R@k; attribute accuracy; relation F1; strata; leakage audit.

**Reference material:**
- the resource cards in `research/briefs/RS-08-ner-landscape.md`;
- `registry/ner_resources.csv`.

Licences: open — TASTEset, RISeC, ARA, ingredient-parser, NYT tagger, GLiNER v2.1; need permission — the CoSyLab repos and the English Recipe Flow Graph corpus.
