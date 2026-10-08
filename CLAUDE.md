# CulinaryState — read first

Local git repository (initialised 2026-10-09; no remote until gate H7 / WP-04). Raw third-party data is never committed (`.gitignore`).

1. `../Plan_SSOT15_v4_0.md` — master plan v4.0 (governs; v2.0 is superseded)
2. `STATUS.md` — current state, blockers (who and what), gate status
3. `DECISIONS.md` — every decision so far (DEC-001…)
4. `docs/DELTA_PLAN_v4.md` — the approved 8-week three-lane plan
5. latest `logs/sessions/*` — last handoff
6. `docs/SSOT_INDEX.md` — SSOT navigation. Never load the SSOT whole (§D4).

Environment: `.venv` (Python 3.12; `requirements.lock.txt`). Run everything from this folder.

**Checks**

| Purpose | Command |
|---|---|
| Tests | `.venv/bin/python -m pytest -o addopts="" -q tests` |
| Lint | `.venv/bin/ruff check src tools tests gate.py app` |
| Gates | `.venv/bin/python gate.py` (PASS / PENDING / FAIL; exit 1 only on FAIL) |

**Builds** (deterministic; inputs pinned by `SNAP-` hashes)

| Builds | Command |
|---|---|
| Registries | `.venv/bin/python tools/seed_registries.py ../Plan_SSOT15_v4_0.md ../computational_gastronomy_master_ssot_v15_0.md` (WP statuses live in this script — DEC-013) |
| Process ontology | `tools/build_proc_v0.py` |
| DEL-1 ledger, data card | `tools/build_del1_ledger.py`; `tools/build_del1_datacard.py` |
| Units | `tools/build_unit_map_v0.py` |
| Molecules | `tools/build_mol_v0.py` |
| Ingredient crosswalk | `tools/build_ing_crosswalk_v0.py` |
| Literature verification queue | `tools/build_lit_verification_queue.py` |

**Experiments**

| Experiment | Command |
|---|---|
| DEL-2 | `tools/run_del2.py [--quick]` → `tools/report_del2.py experiments/DEL2/runs/<id>` (card frozen: `experiments/DEL2/card.md`) |
| DEL-4 dev | `tools/eval_del4_dev.py` |
| DEL-5 dev smoke | `tools/run_ladder_dev.py` (needs local Ollama `qwen2.5:3b`) |
| B15 | `tools/run_b15_rankfreq.py [n_boot]` |
| DEL-3 agreement | `.venv/bin/python tools/del3_agreement.py gold/<r>.A.yaml gold/<r>.B.yaml` |

**Human work**

| Task | Where |
|---|---|
| Literature verification | `ledgers/literature/verification_queue_v0.csv`, guide `docs/annotation/literature_verification_v0.md` |
| Benchmark authoring | `benchmark/authoring/*.yaml`, guide `benchmark/README.md`; `tools/benchmark.py validate|stats|freeze` |
| Demo | `.venv/bin/streamlit run app/demo.py` |

No email, downloads beyond the approved H2 scope (DEC-019), repo, paid API or cluster without H1–H8
approval. The Claude API backend refuses to run without `CULINARYSTATE_H3_APPROVED=1` (DEC-005).
Kush's packages built in Parv's session are Parv-directed work (DEC-020).
