# STATUS — 2026-10-08 (Parv's session) · three-lane format (DEC-034)

Plan + DAG: `docs/LANE_PLAN_v5.md` · Kush's brief: `docs/handoff/KUSH_BRIEF.md` · decisions: DEC-001…038.

**Checks:**
- tests: all pass (see last run in the session log);
- `gate.py`: 0 FAIL;
- ruff: clean.

## A. Lane-A blockers (deadline-critical only)

| Item | Status | Waits on | Unblock | Who |
|---|---|---|---|---|
| DEL-1: ≥ 40 human-verified literature rows | BLOCKED_HUMAN | final human check | work down `ledgers/literature/verification_sheet_v1.csv` (AI-pre-checked; top 60 span 10 families) | Parv + Kush |
| DEL-3 pilot/Gold; session benchmark items; Silver | BLOCKED_EXTERNAL | RecipeDB access | Kush sends `docs/email_drafts/A2.3_bagler_partAS_v4.md` (H1) | Kush |
| DEL-4/5 locked evaluation | BLOCKED_HUMAN | benchmark items + freeze | `benchmark/authoring/` → `tools/benchmark.py freeze` | Parv + Kush |
| Locked ladder runs (Claude API) | BLOCKED_GATE | H3 | after the freeze, with a token estimate | Parv |
| Repo/CI | BLOCKED_HUMAN | H7 | Parv creates the private repo, invites `kushiiitd05` | Parv |

## B. Work continuing despite those blockers

### Done this round

| Task | Result | Artefact |
|---|---|---|
| T01/T02 AI pre-check + sheet | 35 papers, 53 process tables, **1,424 relevant cells (519 high, 523 medium)**, 0 rejected; caught 3 extractor defects (fixed in v1) | `ledgers/literature/ai_precheck_v0.csv`, `verification_sheet_v1.csv`, `candidates_v1.csv` |
| T06 Kinouchi source card | 5 parameters, 27 ambiguities (one internal contradiction); publisher PDF + arXiv preprint, local only | `research/briefs/L13E-kinouchi2008-card.md` |
| T08 Phenol-Explorer audit | no export; terms allow non-commercial research use; maintainer email drafted | ADR 0002 addendum; `docs/email_drafts/PE_maintainers_request.md` |
| T10 research cells | 288 concepts, 6,802 cells; diversified 100-query agenda over 24 classes | `research/cells/priority_cells_v0.csv` |
| T11 (start) process coverage | 12% of relevant literature cells use a treatment missing from `PROC-` (ultrasound, enzymatic pretreatment, heat-moisture treatment, microwave frying, PEF) → proposals | merged pre-check |
| T15 POR- schema | grams only from an exact (ingredient, state, unit, descriptor) record; empty until a portion source is approved | `src/culinarystate/quantity/portion.py` |
| T17 ingredient↔molecule relations | PRESENCE / CONCENTRATION / SENSORY_ASSOCIATION / PROCESS_TRANSITION kept separate | `src/culinarystate/ledger/ingmol.py` |
| T18 reaction ledger | RXN- typed relations; named mechanism needs a quoted source | `src/culinarystate/ledger/reaction.py` |
| T19 tool ledger | 28 TOOL- (identity + process compatibility; physical and safety fields UNKNOWN) | `ledgers/tools/tool_v0.csv` |
| T24 confound tests | frequency-weighted null leaves a residual popularity artefact (z 6); new swap null removes it (DEC-038) | `classical/core.py::curveball` |
| DEL-2 full run | H2 UNDERPOWERED by the frozen rule (19 groups); D7 not promoted; controls pass | `experiments/DEL2/runs/20261008-004800/results.md` |

### Running

| Task | Status |
|---|---|
| — | none: all background agents have finished |

**T09 done:** 18 NER resources carded (13 verified). The RecipeDB3 NER setup differs from the plan: DeBERTa v1 with no CRF, model selected on the test set, SIZE unscored (DEC-039). The first CPU reproductions are listed in the brief.

**T06b done:** the Kinouchi preprint resolves 0 of 27 ambiguities and conflicts with the published version on 3 (DEC-037). **T07 is ready for sign-off:** the simulator is built (`evolution/kinouchi.py`; invariant tests only), and the pre-registration `experiments/B15/kinouchi_v0/prereg.md` is PROPOSED, waiting for Parv to freeze it.

### Next, no gate needed

| Task | What |
|---|---|
| T02b | pre-check the 519 cells new in v1 |
| T05 | search round 2: red meat, poultry, legume first; extract **all** tables, not only cue-word captions |
| T13 | ingredient registry v1 |
| T20 | EDA generator |
| T25 | annotation handbook v1 |
| T29 | registry re-status |
| T21 | AI-draft benchmark candidates, after D2 |

## C. Decisions still open (detail: `docs/LANE_PLAN_v5.md` §5)

| # | Decision |
|---|---|
| D1 | H1: professor email (Kush); Phenol-Explorer request |
| D2 | AI-drafted benchmark candidates allowed, origin-tagged |
| D3 | H2: FoodOn, USDA FoodData Central (portions), FooDB (after a licence check) |
| D4 | H7 repo |
| D5 | H3 later |
| D6 | H8 scope |
| — | Kinouchi: keep the archived publisher copy or delete it (DEC-037); freeze `experiments/B15/kinouchi_v0/prereg.md` (T07) |

## Gate status
- **H1:** nothing sent.
- **H2:** approved for R6, PubChem, PMC/OA papers, FSSAI and Kinouchi; not approved for FoodOn, FDC, FooDB or a Phenol-Explorer crawl.
- **H3:** nothing spent.
- **H7:** no repo.
