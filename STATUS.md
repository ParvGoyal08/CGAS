# STATUS — 2026-10-09 (Parv's session)

Format follows Parv's 9 Oct command. Plan: `docs/LANE_PLAN_v5.md`. Decisions: DEC-001…041. Git: local repo, `main` (no remote until H7).

## Human actions outstanding

| # | Action | Who | Gate |
|---|---|---|---|
| 1 | Approve the exact text of `docs/email_drafts/A2.3_bagler_partAS_v4.md` (v2: seven items, including written permission for the RecipeDB3 artefacts); then Kush sends it | Parv + Kush | H1 |
| 2 | Create the private GitHub repo and invite `kushiiitd05`; give Claude the remote URL, and the local history is pushed | Parv | H7 |
| 3 | Verify ≥ 40 literature cells: start at `verification_queue_ranked_v1.csv`, category P1_VERIFY_NOW (194 ready) | Parv + Kush | DEL-1 |
| 4 | Write benchmark items (human pool). An AI-draft pool is allowed but must be promoted by a human | Parv + Kush | J2 |
| 5 | Kush reviews: process ontology sample, 200 crosswalk aliases, 73 allergen mappings, DEC-001…041 | Kush | review |

## Work completed while waiting

These items are on `main`.

| Item | Artefact |
|---|---|
| DEC-040 RecipeDB3 correction + CR-0003 | `docs/decisions/DEC-040-recipedb3-evaluation-correction.md`; `registry/change_requests.md`; NERRES-03 labelled |
| B08 reproduction card, frozen | `experiments/B08/recipedb3_repro/card.md` (sha in `registry/preregistration.csv`) |
| Professor email v2, send-ready + Kush brief updated | `docs/email_drafts/A2.3_bagler_partAS_v4.md`; brief artefact v2 |
| Kinouchi T07: prereg patched + frozen + run | `experiments/B15/kinouchi_v0/` (prereg, FREEZE, clarifications, results). **NOT REPRODUCED** |
| Internet Archive PDF deleted (metadata kept) | `ledgers/snapshots/l13e_snapshots.jsonl` |
| AI-draft benchmark pool + validator rule | `benchmark/authoring/ai_candidates/README.md`; `tools/benchmark.py validate-ai` |
| Ranked verification queue + HTML report | `ledgers/literature/verification_queue_ranked_v1.csv`; `eda/literature/literature_cell_precheck_report.html` |
| Gate: every frozen prereg is hash-checked | `gate.py` G-PREREG |

## Active parallel work

The 12 background agents (pre-check ×2, handbook, ingredient registry, Agents 1–8) and the round-2 literature download (red meat, poultry, legumes) are listed in the session report.

## Gate changes

| Decision | Item |
|---|---|
| GO | H2-A FoodOn, H2-B FDC (conditions recorded) |
| MODIFY | H2-C ingredient-parser (conditional) |
| GO | AI-draft benchmark pool (separate) |
| DROP | the Internet Archive PDF |
| BLOCKED_EXTERNAL | B08 reproduction (needs written permission) |
| Reported | T07 "reproduced" claim **not supported** under the frozen rule |
