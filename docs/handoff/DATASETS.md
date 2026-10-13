# DATASETS — what exists, where, how big, how it is built

| Dataset | Path | Rows | Built by | Status |
|---|---|---|---|---|
| Evidence v0 (USDA R6) | `ledgers/evidence/evidence_v0.jsonl` | 7,018 (6,994 evaluable) | `tools/build_del1_ledger.py` | frozen (sha in report) |
| Literature candidates v1 | `ledgers/literature/candidates_v1.csv` | 5,955 cells, 35 papers | `tools/reextract_literature_v1.py` | current |
| Literature candidates round 2 | `ledgers/literature/candidates_r2.csv` | 9,147 cells, 24 papers | `… --all-tables --only … --out … --id-prefix LITC2` | not pre-checked |
| AI pre-check | `ledgers/literature/ai_precheck*/` | 2,759 + 113 records | LLM agents (`prompts/precheck/`) | AI only, not verified |
| Verification queue | `ledgers/literature/verification_queue_ranked_v1.csv` | 1,753 (195 VERIFY_NOW) | `tools/rank_literature_queue.py` | awaiting humans |
| Literature evidence | `ledgers/evidence/literature_v1.jsonl` | 0 | `tools/promote_literature.py` | needs signatures |
| Process ontology | `ledgers/process/proc_v0.csv` | 202 | `tools/build_proc_v0.py` | PROPOSED |
| Ingredient crosswalk (A1) | `ledgers/ingredients/alias_a1_v0.csv` | 6,346 names | `tools/build_ing_crosswalk_v0.py` | PROPOSED |
| Units | `ledgers/units/unit_map_v0.csv` | 66 units / 81 variants | `tools/build_unit_map_v0.py` | — |
| Molecules | `ledgers/molecules/mol_v0.jsonl` | 27 | `tools/build_mol_v0.py` | 27/27 InChIKey round-trip |
| Tools | `ledgers/tools/tool_v0.csv` | 28 | `tools/build_tool_v0.py` | PROPOSED |
| Research cells | `research/cells/priority_cells_v0.csv` | 6,802 | `tools/build_research_cells.py` | ordering heuristic |
| Gold fixtures + examples | `gold/` | 18 files | hand-written | `tools/validate_gold.py` 18/18 |
| DEL-2 runs | `experiments/DEL2/runs/` | 2 | `tools/run_del2.py` | results + verdicts |

A global profile of all of these: `.venv/bin/python tools/data_report.py --all` → `eda/global/auto/index.md`.
