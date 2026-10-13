# STATUS — 2026-10-13

**Operating rule:** research, design and automation happen now; human verification and CPU/GPU runs come later. A single blocked task never idles the project.

Decisions: DEC-001…041 · Plan: `docs/LANE_PLAN_v5.md` · Git: local `main` (no remote until H7).

**Professor email: sent by Parv (H1 done, 2026-10-13).** Waiting for RecipeDB / FlavorDB / RecipeDB3 access.

## 1. COMPLETE

| Area | Artefact |
|---|---|
| Registries: 617 items, gates, RS bank, work packages | `registry/` |
| DEL-1 v0: 7,018 USDA R6 rows; schema + validators; data card | `ledgers/evidence/`, `src/culinarystate/ledger/schema.py`, `eda/evidence/v0/` |
| Literature v1: 5,955 verbatim cells from 35 CC-BY papers; 3 extractor defects fixed; AI pre-check of all 35 papers (1,424 relevant cells) | `ledgers/literature/` |
| DEL-2: frozen card, D0–D7 + biased MF, full run. H2 UNDERPOWERED by the frozen rule; controls pass | `experiments/DEL2/` |
| DEL-3 engine: 3 identities, append-only events, replay, observation override, symbolic quantities; gold YAML format + agreement tool | `src/culinarystate/state_graph/` |
| DEL-4 dev: hybrid retrieval, 12-axis compatibility, 5 evidence classes, calibrated abstention | `src/culinarystate/retrieval/` |
| DEL-5: decision layer (7 modes, feasibility, VOI), B0–B5 ladder, 10-scenario Streamlit demo, benchmark kit + AI-draft pool | `src/culinarystate/{decision,eval,demo}/`, `app/`, `benchmark/` |
| Units (66), POR- schema, RXN-, IMAP ingredient–molecule types, TOOL- (28), MOL- (27) | `ledgers/`, `src/culinarystate/{quantity,ledger}/` |
| B03 classical nulls incl. exact-marginal swap null; B15 CSN fit; Kinouchi T07 run (**NOT REPRODUCED** by the frozen rule) | `classical/`, `evolution/`, `experiments/B15/` |
| NER: common span scorer + leakage audit; 18-resource landscape; RecipeDB3 correction (DEC-040); frozen B08 reproduction card | `src/culinarystate/ner/`, `research/briefs/RS-08-ner-landscape.md`, `experiments/B08/` |
| A2 package | `../../Group-17_Assignment_2.zip` |

## 2. ACTIVE now (this session, in priority order)

1. **P1 Evidence:**
   - finish the ranked queue in the five categories, with a conflict queue and a rejected list;
   - extract the round-2 papers (24 new: red meat, poultry, legumes).
2. **P2 Core ID / ledger schemas:** one ID registry for every prefix, validators, and a cross-ledger ID audit.
3. **P10/D4:** the INTERPOLATED and MODEL_ESTIMATED evidence classes. **D5:** Pareto trade-offs.
4. **P5B:** scorer extensions (linking Acc@1/R@5, event/relation F1, quantity/attribute accuracy).
5. **P4:** gold schema, checklist and adjudication template.
6. **P8:** study/source-family split for DEL-2, plus one-command scripts.
7. **P14:** the EDA report generator.
8. **P15:** handoff runbooks (mandatory).

## 3. BLOCKED

| Item | Status | Unblocks when |
|---|---|---|
| DEL-3 gold (40 recipes, 30 sessions); RecipeDB adapter; session benchmark items; Silver runs | BLOCKED_EXTERNAL | RecipeDB access arrives |
| D1 name normalisation to RecipeDB/FlavorDB | BLOCKED_EXTERNAL | RecipeDB + FlavorDB2 name lists |
| RecipeDB3 NER reproduction | BLOCKED_EXTERNAL | written permission |
| ≥ 40 verified literature rows | BLOCKED_HUMAN | Parv/Kush verify from the VERIFY_NOW queue |
| Benchmark (~80 items) | BLOCKED_HUMAN | authoring |
| Peer/chef review | BLOCKED_HUMAN | after the locked runs |
| Phenol-Explorer | BLOCKED_EXTERNAL | maintainer reply, or Parv approves a slow crawl (H2) |
| Locked Claude-API runs | BLOCKED_GATE | H3 (Ollama is enough for the course) |
| Code release | BLOCKED_HUMAN | H7 repo |

## 4. Next 20 highest-value tasks

| # | Task |
|---|---|
| 1 | Queue v1: VERIFY_NOW / STRONG_CANDIDATE / NEEDS_SOURCE / CONFLICT / REJECT, plus `conflict_queue.csv`, `rejected_candidates.csv`, `evidence_precheck_report.html` |
| 2 | Extract the round-2 papers (all tables) → `candidates_r2.csv`; queue them for AI pre-check |
| 3 | Snapshot records for the FoodData Central downloads already on disk |
| 4 | ID registry (all prefixes) + validator + cross-ledger uniqueness audit + tests |
| 5 | Missing schemas: STUDY-, MEAS-, COND-, SVAR-, CLM-, WARN-, SPLIT-, MODEL- |
| 6 | INTERPOLATED evidence class (bracketing conditions only; never extrapolated) |
| 7 | MODEL_ESTIMATED class (flagged tier E7; never in test or calibration sets) |
| 8 | Pareto trade-off ranking over feasible options (unknown values are never imputed) |
| 9 | Recovery scenario "boiled instead of browned" + demo update |
| 10 | Scorer: entity linking Acc@1/R@5, event/relation F1, attribute accuracy, replay metrics |
| 11 | `gold_schema.json`, annotation checklist, adjudication template |
| 12 | DEL-2: study/source-family split + study-level bootstrap code (dry-run on synthetic data only) |
| 13 | Literature promotion script: verified rows → `EvidenceRow` (raw→processed derivation logged) |
| 14 | EDA report generator with plugins |
| 15 | Silver factory skeleton: adapters, validators, duplicate families, 1k→5k→10k gates (no runs) |
| 16 | Handoff: RUNBOOK, MANUAL_NEXT_STEPS, DATASETS, SOURCE_ACCESS, API_BLOCKERS, NER_RUNBOOK, EVIDENCE_REVIEW_GUIDE, GOLD_ANNOTATION_GUIDE, EXPERIMENT_QUEUE, BLOCKERS |
| 17 | AI pre-check of the round-2 papers and the remaining v1-new cells (LLM work, batched) |
| 18 | FoodOn process crosswalk (snapshot exists) |
| 19 | FDC portion → POR- candidates |
| 20 | B14 representation-ladder cards; Jain/Bagler reproduction card |
