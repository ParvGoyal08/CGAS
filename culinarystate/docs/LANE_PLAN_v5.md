# Three-lane execution plan v5 — 2026-10-08

Supersedes the "what's blocking" framing in `STATUS.md`.

- **Rule 1:** a Lane-A blocker never idles the project. Record the blocker and its unblock condition, then move to the next independent Lane-B task. Never touch locked-test labels or bypass a human gate.
- **Status enum** (WP registry + plan): `ACTIVE`, `ACTIVE_PARALLEL`, `BLOCKED_HUMAN`, `BLOCKED_EXTERNAL`, `BLOCKED_GATE`, `BLOCKED_COMPUTE`, `PARKED_POST_COURSE`, `COMPLETE`, `DROPPED_BY_EXPERIMENT`.

## 1. Lane-A blockers (deadline-critical only)

| Item | Status | Waits on | Unblocks when | Owner |
|---|---|---|---|---|
| DEL-1 ≥ 40 human-verified literature rows | BLOCKED_HUMAN | final human check of the AI-pre-checked sheet (T03) | 40 rows have `verifier` + `verified_utc` and G-DEL1-SIZE passes | Parv + Kush |
| DEL-3 pilot + Gold, session benchmark items | BLOCKED_EXTERNAL | RecipeDB / RecipeDB3 access | the professor grants access (email T28, H1) | Kush sends |
| DEL-4/5 locked evaluation | BLOCKED_HUMAN | benchmark items authored and frozen (T22) | `tools/benchmark.py freeze` → G-BENCH PASS | Parv + Kush |
| Locked ladder runs on Claude | BLOCKED_GATE | H3 (spend) | after the freeze; token estimate approved | Parv |
| Repo / CI / collaborators | BLOCKED_HUMAN | GitHub repo created; `kushiiitd05` invited | H7 done (T27) | Parv |

**Not project blockers.**

| Item | Status | Note |
|---|---|---|
| Phenol-Explorer | BLOCKED_EXTERNAL | audit + maintainer request (T08); DEL-1 proceeds on USDA R6 + primary literature |
| DEL-2 H2 claim | COMPLETE: UNDERPOWERED by pre-registered rule | restart = new pre-registration on DEL-1 v1 (T23) |

## 2. Lane B — running now or ready (no gate pending)

**Running now (background agents):** T01 (AI pre-check, 5 agents), T06 (Kinouchi source card), T08 (Phenol-Explorer audit), T09 (NER landscape cards).

**Ready for the main session now:** T10, T11, T13, T15, T17a, T18, T19, T20, T24, T25, T29.

## 3. DAG — next 30 atomic tasks

**Roles**

| Code | Role |
|---|---|
| M | main Claude session |
| A | Claude background agent |
| P | Parv |
| K | Kush |

**Placement**

| Code | Where it runs |
|---|---|
| CPU | laptop CPU |
| IO1 | network, single worker, rate-limited per robots/terms |
| LLM-s | Claude session tokens (included) |
| LLM-l | local Ollama |
| API | paid Claude API (H3) |

| ID | Task | Lane | Depends | Role | Place | Artifact | Done-check | Gate |
|---|---|---|---|---|---|---|---|---|
| T01 | AI pre-check of all process tables in 35 CC-BY papers | B→A | — | A×5 | LLM-s | `ledgers/literature/ai_precheck/*.jsonl` | every cand_id of a PROCESS_EFFECT table has a record; quotes are verbatim XML substrings (script) | — |
| T02 | Merge pre-check; rank a human verification sheet | A | T01 | M | CPU | `ai_precheck_v0.csv`, `verification_sheet_v1.csv` | ≥ 60 high/medium rows across ≥ 8 families; 0 values not equal to `cell_verbatim` | — |
| T03 | Human final verification of ≥ 40 rows | A | T02 | P+K | — | `verifier`/`verified_utc` columns filled | G-DEL1-SIZE PASS | human |
| T04 | Promotion script: verified rows → `EvidenceRow` (E2/E4); concentration→retention only with a raw counterpart, logged as DERIVED | A | T02 (code), T03 (run) | M | CPU | `tools/promote_literature.py`, `evidence_v1` | property test: no value without a verified source cell | — |
| T05 | Literature search round 2, driven by the top research cells | B | T10 | M | IO1 | `candidates_v1.csv` | ≥ 150–250 AI-pre-checked high-quality candidates in total | H2 (PMC ✓) |
| T06 | Kinouchi 2008 original: SRC/SNAP, equations, reproduction card | B | — | A | IO1 | `research/briefs/L13E-kinouchi2008-card.md` | equations quoted with page numbers; ambiguities listed | H2 ✓ |
| T07 | Kinouchi copy–mutate reproduction vs card + A1 corpus | B | T06, P spot-check of the card | M | CPU | `experiments/B15/kinouchi_v0/` | the paper's qualitative curves reproduced within the card's tolerance, or a documented failure | — |
| T08 | Phenol-Explorer route audit + maintainer email draft | B | — | A | IO1 | ADR 0002 addendum; `docs/email_drafts/PE_maintainers_request.md` | licence/route decision recorded | H1 to send |
| T09 | NER resource landscape cards | B | — | A | IO1 | `research/briefs/RS-08-ner-landscape.md`, `registry/ner_resources.csv` | every field verified or marked UNVERIFIED | — |
| T10 | Research-cell ranking: ingredient × process × target | B | — | M | CPU | `research/cells/priority_cells_v0.csv` | ranked from recipe frequency × evidence gap × target class; no dense scrape | — |
| T11 | Process ontology v1: mechanism family, medium, condition axes, endpoint vs action; coverage vs RecipeDB terms + literature process texts | B | T01 | M | CPU | `ledgers/process/proc_v1.csv` + coverage report | coverage reported; no invented concepts | — |
| T12 | FoodOn process crosswalk | B | decision D3 | M | IO1 | `ledgers/process/foodon_xwalk.csv` | each link has an exact FoodOn IRI | **H2 (FoodOn)** |
| T13 | Ingredient registry v1: concept clusters of real corpus names, aliases, ambiguity flags | B | — | M | CPU | `ledgers/ingredients/ing_v1.csv`, `alias_v1.csv` | count = what the corpus supports (no padding); 200-alias audit sample prepared | — |
| T14 | External ingredient crosswalks (FDC, FoodOn, FlavorDB2) | B | decision D3; T28 | M | IO1 | crosswalk CSVs | link precision on a human sample | **H2 / professor** |
| T15 | Quantity ontology v1: count/package/imprecise units, descriptors, regional units; POR- schema | B | — | M | CPU | `ledgers/units/unit_map_v1.csv`, `quantity/` | property tests: no gram without a POR-; unknown locale → interval | — |
| T16 | POR- portion data (USDA FDC portions, CC0) | B | decision D3 | M | IO1 | `ledgers/units/por_v0.csv` | every POR- row has a source span | **H2 (FDC)** |
| T17 | Molecule master v1: formula/mass/descriptors/Morgan for all MOL-; IMAP relation types; add analytes from T02 | B | (a) — (b) T02 | M | CPU+IO1 | `ledgers/molecules/mol_v1.jsonl`, `imap_v1.csv` | InChIKey round-trip 100%; relation type on every IMAP | H2 (PubChem ✓) |
| T18 | Reaction ledger schema RXN- + validator (populated only from verified evidence) | B | — | M | CPU | `src/culinarystate/ledger/reaction.py` + tests | schema rejects a reaction without an evidence id | — |
| T19 | Tool/utensil ledger TOOL- v0 (identity + process compatibility; no physical/safety claims) | B | — | M | CPU | `ledgers/tools/tool_v0.csv` | every safety field = authority id or UNKNOWN | — |
| T20 | Reusable EDA report generator (evidence, ingredients, molecules, processes, units) | B | — | M | CPU | `tools/eda_report.py` → `eda/<ledger>/` | runs on every ledger with no per-ledger code | — |
| T21 | Benchmark candidate pool (AI_DRAFT, separate folder) for evidence task types | A | decision D2 | M | LLM-s | `benchmark/candidates/` | origin-tagged; never auto-enters `authoring/` | — |
| T22 | Human benchmark authoring (evidence types now; session types after T28) | A | T21 optional | P+K | — | `benchmark/authoring/*.yaml` | validator OK; tier reached | human |
| T23 | DEL-2 v2 pre-registration on DEL-1 v1 | A/B | T04 | M | CPU | `experiments/DEL2v2/card.md` | frozen before any v1 outcome is seen | — |
| T24 | B03-lite: frequency/size confound tests over the null cuisines | B | — | M | CPU | `tests/unit/test_classical_confounds.py` | tests pass | — |
| T25 | Annotation handbook v1: event ontology, edges, difficult cases, adjudication protocol (our own fixture texts only) | A prep | — | M | — | `docs/annotation/del3_handbook_v1.md` | every case compiles through `gold.py` | — |
| T26 | Gold-pilot recipe sampling plan (stratified; drawn the day RecipeDB arrives) | A prep | T28 | M | CPU | `docs/annotation/pilot_sampling.md` + script | deterministic sample of 20 | — |
| T27 | Repo bootstrap: `.gitignore`, local `git init`; Parv creates the GitHub repo, invites `kushiiitd05` | A | Parv's OK to commit | P (+M) | — | repo URL | CI green on the first push | **H7** |
| T28 | Send the professor email | A | both approve the text | K | — | sent mail | reply logged | **H1** |
| T29 | Re-status all 617 registry items with the new enum + restart conditions | B | — | M→K review | CPU | `registry/experiments.csv` | seeder assertion passes | — |
| T30 | Lane-C prep: §257P Silver-pilot checklist + token/cost estimate | C | T28 | M | CPU | `docs/lane_c/silver_pilot_readiness.md` | every checkbox has evidence or "missing" | H3 later |

**Critical paths**

| Path | Sequence |
|---|---|
| DEL-1 | T01 → T02 → **T03 (human)** → T04 → T23 |
| DEL-3 | **T28 (H1)** → access → T26 → pilot |
| DEL-5 | T21 → **T22 (human)** → freeze → **H3** → locked runs |

## 4. Who needs whom

| Task | Needs |
|---|---|
| T03 human verification | **Parv + Kush** (≈ 40–60 rows) |
| T22 authoring | **Parv + Kush** |
| T07 card spot-check | **Parv** |
| Reviews: P2 ontology, crosswalk sample, allergen lexicon | **Kush** |
| T27 repo | **Parv** creates; **Kush** accepts the invite |
| T28 email | **Kush** sends |
| Everything else | neither — runs in the Claude session |

## 5. Decisions still open

| # | Decision | Recommendation |
|---|---|---|
| D1 | H1: send the professor email (Kush) and, later, the Phenol-Explorer email | send the professor email now |
| D2 | AI-drafted benchmark *candidates*. The master plan does not forbid them (AH13 only requires the curator role) | allow in `benchmark/candidates/` with `origin: AI_DRAFT`. A human must rewrite or approve each item before it enters `authoring/`; results are reported per origin; prefer human-origin items for the locked test (contamination: the system under test is an LLM) |
| D3 | H2 for new sources: **FoodOn** (CC BY 4.0, ontology OWL/OBO), **USDA FoodData Central** (CC0; portions/foods), **FooDB** (licence to check) | approve FoodOn + FDC; FooDB after a licence check |
| D4 | H7: create the private GitHub repo `culinarystate` under Parv's account, invite `kushiiitd05`; allow a local `git init` + first commit | yes |
| D5 | H3: Claude API spend for the locked runs | later — after the freeze, with a token estimate |
| D6 | H8: scope stays three-lane per v4.0 | confirm |
