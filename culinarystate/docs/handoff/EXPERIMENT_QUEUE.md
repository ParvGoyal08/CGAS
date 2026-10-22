# EXPERIMENT_QUEUE — every unfinished task (2026-10-13)

Run everything from `Project/culinarystate/` with `.venv/bin/python`. "Claude" means a Claude Code session in this repo. Tasks are in dependency order within each deliverable.

## D1 — Evidence ledger

| Field | Q1. Human verification of literature cells |
|---|---|
| **WHY** | The brief requires ≥ 40 hand-verified literature rows |
| **INPUT** | `ledgers/literature/verification_queue_ranked_v1.csv`, rows with `queue_category == VERIFY_NOW` (195) |
| **COMMAND** | Edit the CSV: fill `is_retention_relevant`, `verifier`, `verified_utc`; correct mappings in `final_*` columns. Guide: `EVIDENCE_REVIEW_GUIDE.md` |
| **OUTPUT** | Signed rows |
| **CHECK** | `tools/promote_literature.py` reports `meets_DEL1_40: true` |
| **HUMAN** | Parv + Kush, ~1.5 h |
| **COMPUTE** | none |
| **NEXT** | Q2 |

| Field | Q2. Promote verified rows |
|---|---|
| **WHY** | Turns verified cells into `EvidenceRow`s (E2/E4) |
| **INPUT** | the signed queue |
| **COMMAND** | `.venv/bin/python tools/promote_literature.py` |
| **OUTPUT** | `ledgers/evidence/literature_v1.{jsonl,report.json,rejects.csv}` |
| **CHECK** | `rejects.csv` reviewed; `gate.py` G-LEDGER and G-IDS PASS |
| **HUMAN** | fix rejected rows (usually: map the process) |
| **COMPUTE** | seconds |
| **NEXT** | Q3 |

| Field | Q3. Build and freeze evidence v1 |
|---|---|
| **WHY** | DEL-1 v1 = USDA R6 + literature (+ Phenol-Explorer if acquired) |
| **INPUT** | `evidence_v0.jsonl`, `literature_v1.jsonl` |
| **COMMAND** | **to write**: `tools/build_evidence_v1.py`. It concatenates, re-validates, writes `evidence_v1.jsonl` + report, and pins the sha in `registry/datasets.csv` |
| **OUTPUT** | `ledgers/evidence/evidence_v1.*` |
| **CHECK** | `tools/data_report.py evidence` shows 0 validation failures |
| **HUMAN** | approve the freeze |
| **COMPUTE** | seconds |
| **NEXT** | Q4, D2-Q1 |

| Field | Q4. Data card v1 |
|---|---|
| **WHY** | The brief requires a coverage and bias report |
| **INPUT** | `evidence_v1` |
| **COMMAND** | `tools/build_del1_datacard.py` (point `LEDGER` at v1) + `tools/data_report.py --all` |
| **OUTPUT** | `eda/evidence/v1/` |
| **CHECK** | the report lists sources, tiers, condition completeness and bias |
| **HUMAN** | read and sign off |
| **COMPUTE** | seconds |
| **NEXT** | report |

| Field | Q5. AI pre-check of round-2 papers + 6 unfinished v1-new papers |
|---|---|
| **WHY** | 9,147 round-2 cells (red meat, poultry, legumes) are not yet pre-checked |
| **INPUT** | `candidates_r2.csv`, `candidates_v1.csv` |
| **COMMAND** | an LLM agent with `prompts/precheck/precheck_prompt.md`, 5–9 papers per agent; then `tools/rank_literature_queue.py` |
| **OUTPUT** | `ledgers/literature/ai_precheck_r2/*.jsonl` and `ai_precheck_v1new/*.jsonl` |
| **CHECK** | the ranker counts the new papers; quotes verbatim (0 rejected) |
| **HUMAN** | none (AI pre-check) |
| **COMPUTE** | LLM session tokens |
| **NEXT** | Q1 (more candidates) |

| Field | Q6. Phenol-Explorer |
|---|---|
| **WHY** | Named in D1; the only route to study-disjoint splits |
| **INPUT** | the maintainer reply, or approval of a crawl |
| **COMMAND** | **to write**: `tools/ingest_phenol_explorer.py` (≤ 1 request / 10 s) |
| **OUTPUT** | Phenol-Explorer evidence rows with `STUDY-` ids |
| **CHECK** | rows validate; every row cites its publication |
| **HUMAN** | send the email (`docs/email_drafts/PE_maintainers_request.md`) **or** approve a crawl (H2) |
| **COMPUTE** | hours of polite IO |
| **NEXT** | D2-Q1 |

| Field | Q7. Name normalisation to RecipeDB / FlavorDB |
|---|---|
| **WHY** | The brief's D1 check |
| **INPUT** | RecipeDB + FlavorDB2 name/ID lists from the professor |
| **COMMAND** | **to write**: a join of `ING-` → RecipeDB/FlavorDB ids, extending `tools/build_ing_crosswalk_v0.py` |
| **OUTPUT** | `ledgers/ingredients/xref_recipedb_flavordb.csv` |
| **CHECK** | `tools/data_report.py ingredient`: share linked; 100 links checked by a human |
| **HUMAN** | spot-check |
| **COMPUTE** | seconds |
| **NEXT** | report |

## D2 — Sparsity-aware completion

| Field | D2-Q1. Pre-register and run DEL-2 v2 |
|---|---|
| **WHY** | Study-disjoint split + study-level bootstrap (brief) |
| **INPUT** | the frozen `evidence_v1` with study ids |
| **COMMAND** | write `experiments/DEL2v2/card.md` (copy the v1 card and add the `study` and `source_family` splits, already implemented in `transition/del2.py`); freeze its sha in `registry/preregistration.csv` **before** any run; then `tools/run_del2.py` (point it at v2) and `tools/report_del2.py <run>` |
| **OUTPUT** | `experiments/DEL2v2/runs/<id>/results.md` |
| **CHECK** | `gate.py` G-PREREG PASS; ≥ 30 groups, or the verdict is "UNDERPOWERED" |
| **HUMAN** | approve the card |
| **COMPUTE** | CPU ~30–60 min |
| **NEXT** | report |

## D3 — State tracking

| Field | D3-Q1. RecipeDB adapter |
|---|---|
| **WHY** | The engine must consume structured recipe tables |
| **INPUT** | RecipeDB access |
| **COMMAND** | **to write**: implement `RecipeDBAdapter.iter_recipes` in `src/culinarystate/silver/pipeline.py`; a table → event-draft converter |
| **OUTPUT** | recipes as `{recipe_id, ingredients, steps}` |
| **CHECK** | 20 recipes load |
| **HUMAN** | none |
| **COMPUTE** | seconds |
| **NEXT** | D3-Q2 |

| Field | D3-Q2. Gold: 40 recipes + 30 sessions |
|---|---|
| **WHY** | The brief's D3 evaluation set |
| **INPUT** | RecipeDB recipes (stratified sample) |
| **COMMAND** | annotate per `GOLD_ANNOTATION_GUIDE.md`; `tools/validate_gold.py gold/`; double-annotate 10 → `tools/del3_agreement.py A B` |
| **OUTPUT** | `gold/<id>.yaml` + `gold/adjudication/` |
| **CHECK** | all files validate; agreement reported |
| **HUMAN** | ~25 h total |
| **COMPUTE** | none |
| **NEXT** | D3-Q3 |

| Field | D3-Q3. State-accuracy evaluation |
|---|---|
| **WHY** | State-field accuracy, replay consistency, merge/split F1 |
| **INPUT** | gold + system output (oracle events; LLM extractor) |
| **COMMAND** | **to write**: `tools/eval_del3.py` (replay digest equality; `state_graph.agreement`; `ner.scorer.attribute_accuracy`) |
| **OUTPUT** | `experiments/DEL3/results.md` |
| **CHECK** | numbers for oracle vs automatic upstream |
| **HUMAN** | none |
| **COMPUTE** | CPU minutes (+ local LLM) |
| **NEXT** | report |

## D4 / D5 — Retrieval and end-to-end system

| Field | D5-Q1. Benchmark (~80 items, 8 task types) |
|---|---|
| **WHY** | The brief's D5 benchmark |
| **INPUT** | evidence v1; RecipeDB sessions |
| **COMMAND** | write `benchmark/authoring/*.yaml` (AI drafts allowed only in `ai_candidates/`, promoted by a human); `tools/benchmark.py validate`, `stats`, then `freeze` once |
| **OUTPUT** | `benchmark/{dev,test}.jsonl` + `FROZEN.sha256` |
| **CHECK** | `gate.py` G-BENCH PASS |
| **HUMAN** | ~7 h |
| **COMPUTE** | none |
| **NEXT** | D5-Q2 |

| Field | D5-Q2. Locked ladder B0–B5 + ablations + oracle + robustness |
|---|---|
| **WHY** | The brief's D4/D5 results |
| **INPUT** | the frozen benchmark |
| **COMMAND** | **to extend**: `tools/run_ladder_dev.py` into a locked runner (reads `benchmark/test.jsonl`; systems B0–B5; ablation flags; oracle state/evidence; ~16 paraphrase/unit/constraint variants) |
| **OUTPUT** | `experiments/DEL5/locked/` |
| **CHECK** | test touched once; results per frequency stratum (`ner.scorer.frequency_strata`) |
| **HUMAN** | none |
| **COMPUTE** | local Ollama, hours. Claude API only with H3 |
| **NEXT** | D5-Q3 |

| Field | D5-Q3. Chef/peer review |
|---|---|
| **WHY** | The brief's human evaluation |
| **INPUT** | about 40 shuffled B3/B5 answers |
| **COMMAND** | **to write**: a blind rating sheet (CSV); agreement between reviewers |
| **OUTPUT** | `experiments/DEL5/review/` |
| **CHECK** | ≥ 2 raters; agreement reported |
| **HUMAN** | 2–3 people × 1 h |
| **COMPUTE** | none |
| **NEXT** | report |

| Field | D4-Q1. Neural dense retriever |
|---|---|
| **WHY** | "Dense" is LSA today |
| **INPUT** | a small embedding model (e.g. all-MiniLM-L6-v2, Apache-2.0) — **record the model licence and sha first** |
| **COMMAND** | **to write**: a `dense` option in `retrieval/core.py`; rerun `tools/eval_del4_dev.py` |
| **OUTPUT** | DEL-4 dev metrics |
| **CHECK** | hybrid Recall@5 not worse than LSA |
| **HUMAN** | approve the model download |
| **COMPUTE** | CPU minutes |
| **NEXT** | D5-Q2 |

## Lane B (non-blocking)

| Task | Command | Status |
|---|---|---|
| FoodOn process crosswalk | **to write** from `data/raw/foodon/foodon.owl` (SNAP-FOODON-0001) | FoodOn on disk |
| FDC portions → POR- candidates | **to write**; FDC on disk (SNAP-FDC-0001/0002; licence quote still to record) | — |
| NER baselines | see `NER_RUNBOOK.md` | — |
| Silver 1k pilot | `run_stage(1000, RecipeDBAdapter(), llm, approved_h3=True, out_dir=…)` after RecipeDB + H3 | gated |
| B15 | Kinouchi follow-up question to the authors (A1/A17), needs H1; Jain/Bagler reproduction card | — |
| B14 representation ladder cards (binary → … → state graph) | card only, no runs | — |
