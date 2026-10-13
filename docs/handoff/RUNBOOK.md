# RUNBOOK — setup, checks and every command

**Setup**

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.lock.txt
ollama pull qwen2.5:3b        # only for LLM runs
```

**Health checks** (run before and after any change)

```bash
.venv/bin/python -m pytest -o addopts="" -q tests      # all tests
.venv/bin/ruff check src tools tests gate.py app        # lint
.venv/bin/python gate.py                                # gates: snapshots, ledger, prereg, ids, units, replay, …
.venv/bin/python tools/audit_ids.py                     # id formats / reuse / dangling refs
.venv/bin/python tools/data_report.py --all             # global data report
```

**By deliverable**

| Deliverable | Command |
|---|---|
| D1 ledger | `tools/build_del1_ledger.py` → `tools/build_del1_datacard.py` |
| D1 literature | `tools/reextract_literature_v1.py` → AI pre-check (prompt) → `tools/rank_literature_queue.py` → humans sign → `tools/promote_literature.py` |
| D2 | `tools/run_del2.py [--quick]` → `tools/report_del2.py experiments/DEL2/runs/<id>` (card must be frozen first) |
| D3 | `tools/validate_gold.py gold/` · `tools/del3_agreement.py gold/<r>.A.yaml gold/<r>.B.yaml` |
| D4 | `tools/eval_del4_dev.py` (dev, synthetic queries) |
| D5 | `tools/run_ladder_dev.py` (dev smoke) · `tools/benchmark.py validate|validate-ai|stats|freeze` · demo: `.venv/bin/streamlit run app/demo.py` |
| B15 | `tools/run_b15_rankfreq.py [n_boot]` · `tools/run_kinouchi.py` (refuses if the prereg changed) |

**Rules that must never be broken**
- Pre-registration before data. Changing a frozen file fails G-PREREG.
- Never invent values; UNKNOWN stays UNKNOWN.
- AI pre-check ≠ human verification.
- No test-set selection.
- Raw third-party data is never committed.
- No email, new data source, paid API or repo push without its gate (H1/H2/H3/H7).
