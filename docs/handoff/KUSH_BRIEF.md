# Brief for Kush — CulinaryState-RAG (Group 17), 8 Oct 2026

From Parv. This covers where the project stands, the four things only you can do, and how to start working in the repo.

## Where we are (one minute)

- The machine side of all five deliverables is built and tested: **165 tests pass**, and `gate.py` reports 7 PASS, 4 PENDING, 0 FAIL.
  - **DEL-1:** the USDA R6 ledger (7,018 rows).
  - **DEL-2:** pre-registered and run. H2 is "underpowered" by our own frozen rule, because there are only 19 ingredient groups.
  - **DEL-3:** the state engine.
  - **DEL-4:** retrieval with abstention.
  - **DEL-5:** the B0–B5 ladder and a 10-scenario demo.
- Your work packages (K1–K17) were built in Parv's session as **Parv-directed work** (DEC-020). You are the reviewer for those and can take any of them over.
- **What we are waiting on is people, not code:**
  - your email to the professor (RecipeDB access);
  - human verification of literature rows;
  - human-written benchmark items;
  - the GitHub repo.
- Everything else continues in parallel (`docs/LANE_PLAN_v5.md`, 30-task DAG).

## Your four items, in priority order

### 1. Send the data-access email to Prof. Bagler (gate H1) — today if you can

- **File:** `docs/email_drafts/A2.3_bagler_partAS_v4.md` (version 2, 9 Oct). It contains seven requests, including **written permission** for the unlicensed RecipeDB3 GitHub artefacts. Send it only after both of you approve the exact text.
- **Before sending, tick its three boxes:**
  - remove anything he has already granted;
  - check the sender line: you send it, with Parv in cc;
  - confirm the RecipeDB 3.0 support address on the current docs page (the Postman docs list `bagler@iiitd.ac.in`).
- Send it from your IIIT-D address. Then forward any reply to Parv.
- **Why it matters:** RecipeDB unblocks:
  - the DEL-3 annotation pilot and Gold;
  - all session-type benchmark items;
  - the 10k Silver pilot.

### 2. GitHub (gate H7)

- Your username **`kushiiitd05`** is recorded.
- Parv will create a private repo `culinarystate` and invite you. **Accept the invite.**
- Then set up your environment:

  ```bash
  git clone <repo-url> && cd culinarystate
  python3.12 -m venv .venv && .venv/bin/pip install -r requirements.lock.txt
  .venv/bin/python -m pytest -o addopts="" -q tests     # expect all green
  .venv/bin/python gate.py                              # expect 0 FAIL
  .venv/bin/streamlit run app/demo.py                   # the demo
  ```

- Read these first: `CLAUDE.md` → `STATUS.md` → `docs/LANE_PLAN_v5.md` → `DECISIONS.md`.

### 3. Reviews (you are the named reviewer)

| What | File | What to check | Record your decision |
|---|---|---|---|
| Process ontology v0 (202 `PROC-`, 270 RecipeDB terms classified) | `ledgers/process/recipedb_term_map_v0.csv`, `proc_v0.csv` | Each RecipeDB term → PROC / AMBIGUOUS / non-process. A sample of 50 is fine | Add a `review` column (ok / wrong: why) |
| Ingredient crosswalk (A1 vocab → USDA R6 categories) | `ledgers/ingredients/alias_a1_v0.csv` | 200 aliases, stratified by `rule_id` | Same `review` column |
| Allergen lexicon | `ledgers/authority/allergen_lexicon_v0.csv` | The **8 allergen classes come only from FSSAI** (Labelling & Display Regs, Reg. 5(14), verbatim). FlavorDB is never the safety authority. 21 terms are listed in the regulation itself. **73 terms are Claude's suggested mappings** of ingredient words onto those FSSAI classes (e.g. "cashew" → tree nut), marked `INFERRED_LLM` | Approve or reject each of the 73 |
| Decisions | `DECISIONS.md` | DEC-001…032 are PROPOSED or APPROVED by Parv. In particular, confirm DEC-018 (agreement gate F1 ≥ 0.80) | Write "Kush: agree" or your objection |

### 4. Human verification of literature rows (DEL-1 needs ≥ 40)

You will **not** research 80 papers from scratch.

- Claude has copied **5,435 table cells verbatim** from 35 open-access (CC BY) papers.
- It is running an **AI pre-check** on every processing table, recording for each cell:
  - food, process, conditions, target, units and basis;
  - a verbatim quote from the paper.
- The result is a ranked sheet: `ledgers/literature/verification_sheet_v1.csv`. It is ready once the pre-check finishes.

**Your job:** take about 20–30 rows. For each one:

1. Open the paper (`europepmc.org/article/PMC/<pmcid>`).
2. Find the cell, and check that the number and the mapping are correct.
3. Fill `is_retention_relevant`, `verifier`, and `verified_utc`.

Guide: `docs/annotation/literature_verification_v0.md`. Expect about 1–2 minutes per row.

**Rule:** put your name in `verifier` only if **you** checked the cell against the paper. AI pre-check is not human verification, and we never label it as such.

## Optional, when you have time

- **Benchmark items:** write evidence-type questions in `benchmark/authoring/kush_01.yaml` (format in `benchmark/EXAMPLE_items.yaml`), then run `.venv/bin/python tools/benchmark.py validate`. Session-type items wait for RecipeDB.
- **Ownership:** take over any K-package you want to own going forward. Tell Parv, and it is recorded in `DECISIONS.md`.

## Two things to know

- **Gates:** nothing is sent, published, purchased or run on paid APIs without the matching gate:
  - H1: email;
  - H2: new data source;
  - H3: Claude API spend;
  - H7: repo.
- **A2:** if you are the person who submitted A1, **you** must upload `Group-17_Assignment_2.zip` (the rubric deducts 2 marks otherwise). Parv has the file.
