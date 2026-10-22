# DEL-5 benchmark: authoring guide (J2)

**Authors:** Parv and Kush. Every item is written by a human. No tool and no LLM drafts, edits
or suggests item text, because the system under test must never have seen machine-made versions
of its own test questions.

**Tiers (AH5):**

| Tier | Items | Split |
|---|---|---|
| floor | 104 | 13 per task type |
| target | 320 | 80 dev + 240 test |
| stretch | 440 | — |

Decide target versus floor at the W3 d5 checkpoint, from the measured rate on the first 40
items. Freeze on W4 d5.

## How

1. Write items in `benchmark/authoring/<you>_<batch>.yaml`. The format is in `EXAMPLE_items.yaml`.
2. Run `.venv/bin/python tools/benchmark.py validate` until it prints `OK`. It checks:
   - required fields are present;
   - every enum value is valid;
   - author ≠ reviewer;
   - evidence IDs exist in the ledger;
   - abstain items have no evidence and use gold mode ABSTAIN;
   - session items name a RecipeDB recipe;
   - `FIX-` fixtures are refused (they appear in the tests and demo);
   - no question is a near-copy of a demo scenario.
3. Run `.venv/bin/python tools/benchmark.py stats` to see counts per task type and the tier reached.
4. **Freeze (curator only, once):** `tools/benchmark.py freeze`. It:
   - splits each task type 25/75 into dev/test, deterministically by item-ID hash;
   - writes `dev.jsonl`, `test.jsonl` and `FROZEN.sha256`;
   - appends a row to `registry/preregistration.csv`.

   `gate.py` then reports `G-BENCH PASS`. **From that point nothing is tuned on test labels.**
   The curator knows the items but does not tune on them (AH13).

## Coverage per task type

Aim for these spreads within each task type:

| Dimension | Spread |
|---|---|
| Difficulty | easy / medium / hard |
| Evidence regime | `observed`, `near`, `unsupported` (+ `conflict` once a second source is verified) |
| Ingredient families | ≥ 6 of the 12 anchor families |

Session tasks (state, next_action, constraints, diagnosis, recovery) need RecipeDB recipes, so
they are **blocked until access arrives**. Evidence tasks (process_effect, abstain) can be
written now against `ledgers/evidence/evidence_v0.jsonl`. Conflict items need the verified
literature rows (K8).
