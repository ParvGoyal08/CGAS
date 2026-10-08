# Delta plan — master prompt v4.0 (Parts AG–BB) applied to the 8-week CulinaryState plan

## Context

The user supplied `Project/Plan_SSOT15_v4_0.md` (4,879 lines). Parts A–AF are
identical to v2.0. The new Parts AG–BB review the previous 8-week plan (built
from the user's decisions D-1…D-6) and correct it. **Part AU** asks for exactly
this artefact:

> "Produce a **delta plan**, not a new unrelated plan. Resolve the AH
> corrections, seed all registries, and show: (1) the updated Lane A critical
> path; (2) Lane B parallel foundation jobs; (3) every blocked/deferred block
> with restart gate; (4) data/API/licence blockers; (5) compute placement;
> (6) benchmark target tier; (7) the next seven atomic work packages with
> owner/reviewer. Then stop for human approval."

The registries cannot be written in plan mode, so seeding them is **WP-01**, the
first action after approval.

### Direct answer to "are you making the full 100k datasets with temperature simulation?"

Per v4.0, **not inside the 8 weeks**, and not by fabrication at any point:

| Item | Lane | When |
|---|---|---|
| 60k → 100k Silver recipe corpus | **C** | post-course, staged 25k → 60k → 100k, each gated (Part BA) |
| 10k Silver pilot | **B** | inside the 8 weeks. GO/BLOCKED at the W3 gate on the §257P checklist; runs in stages 1k → 5k → 10k in W5 (AP3) |
| ≥100k tiered evidence rows | **C** | "if evidence sources genuinely support it" (BA); course target is 5k–10k rows (AH7) |
| Temperature/time **evidence** | **A/B** | every row stores T/t as `MEASURED` / `RANGE` / `QUALITATIVE` / `UNKNOWN`. Kinetic parameters (Ea, k, order, T range) for focused systems (SX-06-04) are collected as evidence rows in B06 expansion |
| Temperature **simulation** (kinetic models, hybrids, simulator pretraining) | **C** | SSOT ladder D8–D11 after G15-4/5; synthetic data only through G15-10; outputs are tier E7 `SIMULATED` and never enter test/calibration sets |

### Inconsistencies found in v4.0 (raised, not silently resolved — §A3)

| # | Issue | Handling |
|---|---|---|
| X1 | **AZ6's transition ladder contradicts the SSOT.** AZ6: D1 process mean, D2 nearest, D3 linear/tree, D4 neural residual… The SSOT (L18547–18609, rank 1): D1 global mean-delta, D2 process-conditioned mean-delta, D3 hierarchical shrinkage, D4 nearest-evidence, D5 GBDT, D6 TabPFN, D7 completion, D8 kinetics, D9 hybrid, D10 multi-output, D11 UDE/ODE. v4.0's own AI6 matches the SSOT | **Follow the SSOT.** Record a master-prompt fix in `DECISIONS.md` |
| X2 | Part AU says to load `CulinaryState_Detailed_RnD_Execution_Plan_v2.md` and `…Final_Execution_Plan_v3_0.md`; AG4 ranks the detailed R&D plan 4th. **Neither is in `Project/`.** The merged compiler plan (E0–E14) is also absent | Proceed without them; their IDs → `BLOCKED_EXTERNAL`. Send them if they exist |
| X3 | AK1 asks to seed "JEPA J1–J5". **No such IDs exist in the SSOT** (0 matches) | Seeded as `BLOCKED_EXTERNAL` (source document not provided) |

The user's decisions still stand. **D-1 is revised by AG** from "course + deferred
roadmap" to three lanes. D-2…D-6 are unchanged: 8 weeks; RecipeDB for DEL-3;
required-APIs email (now the Part AS text); Ollama for development + Claude API
for the locked runs; Part S2 split.

---

## 0. Delta table — previous plan → v4.0

| Area | Previous plan | v4.0 delta | Part |
|---|---|---|---|
| Scope | DEL-1…5; B03/B04/B07/B08/B15 deferred | **Three lanes:** A course-critical, B parallel foundations, C gated scale. Nothing deleted; every SSOT item gets a status (`ACTIVE_COURSE`, `ACTIVE_PARALLEL`, `BLOCKED_EXTERNAL`, `BLOCKED_GATE`, `PARKED_POST_COURSE`, `DROPPED_BY_EXPERIMENT`, `COMPLETE`) plus a restart condition | AG |
| `EvidenceRow` lineage | `study_ids` non-empty | `origin_type ∈ {PRIMARY_STUDY, DATABASE_AGGREGATE, REVIEW_AGGREGATE, AUTHORITY_STANDARD, PROJECT_MEASUREMENT}`; **`source_family_id` required**; `study_ids` optional for aggregates and never fabricated | AH1 |
| Ingredient identity | canonical name + FlavorDB/RecipeDB link or `UNRESOLVED` | **internal `ING-` first**; external crosswalks optional; `UNRESOLVED_EXTERNAL` allowed | AH2 |
| Allergens | FlavorDB categories + an authority list | **`ALLERGEN-` table from FSSAI only**; FlavorDB is never a safety authority | AH3 |
| Conformal | "coverage within ±5 pts of nominal 90%" threshold | report **empirical** coverage and width per split; no nominal-validity claim under shift; weighted/shift-aware conformal only as an experiment | AH4 |
| Benchmark | 80 test + 24 dev | tiers: **minimum 104 / target 320 (80 dev + 240 test) / stretch 440**; achieved tier reported | AH5 |
| DEL-3 Gold | 40 recipes + 30 sessions | + **20-recipe design pilot in W2**; target 100–160 Gold/Gold-Light, 80–100 sessions | AH6, AI4 |
| DEL-1 size | ≥1k + ≥40 verified | target **5k–10k rows + 100–150 verified**; a **12-family anchor matrix** replaces the 6 anchors | AH7, AI5 |
| B03 | deferred | **B03-lite W1–W2** | AH8 |
| B04 | deferred | **B04-lite**: `MOL-` schema, structures for touched molecules, RDKit fingerprints, `IMAP-` joins | AH9 |
| B07 | deferred | **10k Silver pilot**, Lane B, GO/BLOCKED at W3 | AH10, AP |
| B08 | deferred | scorer + one matched reproduction + split audit + oracle-span test | AH11, AQ3, AW |
| B15 | deferred | one bounded chain if capacity allows | AH12 |
| Test lock | "nobody opens `test.jsonl`" | **curator-role language**: after the hash freeze, nothing is tuned from test labels; the curator knows the items but does not tune | AH13 |
| Claim scoring | humans 50% / LLM 50% | **double-annotated** stratified human subset; LLM judge supplemental; agreement reported | AH14 |
| External facts | facts table in the plan | `SNAP-`/`API-` entries with timestamps, re-verified at W0 | AH15 |
| DEL-2 cell | (food, process, target) | an **explicit projection** of the full cell `(matrix, S_in, process, Θ, target, basis)`, with condition-completeness masks; RF semantics fields; study-component graph with fallback; propensity sensitivity; promotion rule | AM |
| DEL-3 | entities + belief fields | **three identities** (concept / lot / version); `trajectory ∈ {PLANNED, OBSERVED_SESSION, PREDICTED}`; `OMITTED_STEP_CANDIDATE` | AN |
| DEL-4/5 | RRF retrieval, 4-axis compatibility | **compiled retrieval packet** (11 sections); **12-axis inspectable compatibility**; `CLM-` per claim; 7 decision modes; B6/B7 only if gated; demo ≥8, target 12–16 | AO, AI8–9 |
| WPs | K1–K14, P1–P11, J1–J5 | **K1–K17, P1–P15, J1–J8** | AJ |
| Email | Appendix A (my draft) | **Part AS text** (adds FlavorDB2 molecule mappings and RecipeDB3 model/notebook artefacts) | AS |

---

## 1. Updated Lane A critical path

`→` marks the critical-path dependency.

| Wk | Lane A work (owner) | Week gate |
|---|---|---|
| W0 | registries seeded (Parv); `DECISIONS.md`; repo + collaborators (Kush, **H7**); AS email (Kush, **H1**); `SNAP-` re-verification (Kush) | no scraping, paid API or cluster job before approval |
| W1 | CI + schemas v1 (AH1/AH2) + `gate.py` (K1/K3); USDA R6 snapshot + profile (K2); Phenol-Explorer ADR (K4); process ontology v0 (P2); **append-only event core** (P3); annotation guideline v0 (P4) | a broken row is rejected by CI; raw hash pinned; internal IDs work without RecipeDB/FlavorDB; **one fixture source → row → query → citation end to end** |
| W2 | DEL-1 v0 ingestion; RF > 1 not clipped; aggregates typed `DATABASE_AGGREGATE` (K5); quantity grammar + symbolic split/reserve (K7); **20-recipe Gold design pilot**, double-annotated, no pre-fill → handbook fixes (P4, J3); replay determinism tests | 20 recipes fit the schema without ad-hoc fields; **0 invented grams**; replay deterministic |
| W3 | DEL-1 scale: 12-family anchor matrix, verified literature rows (K8) → **DEL-1 v1 freeze** (K9); DEL-2 cell/inclusion/study-component graph/propensity features/D0–D7 cards frozen **before any test metric** (P5); RecipeDB adapter + candidate pool (P6) | DEL-2 cards committed; no locked-split result inspected; evidence v0/v1 frozen |
| W4 | DEL-2 runs D0–D7 + biased MF on pair, ingredient, study-component and random-sanity splits (P7); DEL-3 course Gold double-annotated, agreement before adjudication (J3); BM25 + dense + structured + RRF + compatibility scorer (K10); **benchmark freeze at the achieved tier** (J2) | test hash frozen; curator role recorded; dev/calibration/test separation documented |
| W5 | **DEL-2 close** (P8: KEEP/MODIFY/DROP/NEED_DATA); **DEL-3 close** (P9: field accuracy, replay, edge F1, allocation accuracy, unresolved rate, oracle-vs-built gap); 8-axis compatibility + evidence cascade + calibration (K11) | DEL-2 and DEL-3 gate verdicts |
| W6 | **DEL-4 locked evaluation** (K12); decision layer with 7 modes, authority-backed feasibility, separated proposer/verifier, recovery evidence (P10) | **B5 must earn itself on dev**, or B4/B3 is kept and the result reported |
| W7 | locked ladder B0–B5 (+B6/B7 only if gated) on the Claude API (**H3**) (K13/K14); ablations; oracle state/evidence/events; human review (J4); demo (P11) | no final claim without a `CLM-`, experiment ID, artefact hash and CI/gate verdict |
| W8 | buffer: reproducibility fixes only, clean rerun, cards, EDA, claim ledger, report/poster, contribution audit, final scope report, Phase-2 backlog (J5, J8) | §257P final-claims checklist |

## 2. Lane B — parallel foundation jobs (never block Lane A)

| Job | WP | Owner → reviewer | Weeks | Entry gate | Output | Stop if |
|---|---|---|---|---|---|---|
| B03-lite classical regression | K15 | Kush → Parv | W1–W2 | — | tested binary-membership invariant; null-cuisine + A2 frequency-control regression tests (reusing `A2/src/random_controls.py`); `N_s` + fingerprint/Tanimoto smoke test **where molecule data exist** | — |
| B04-lite molecule registry | K16 | Kush → Parv | W1–W3 | — | `MOL-` schema (InChIKey, canonical SMILES); structures for every molecule touched by DEL-1. Phenol-Explorer has 161 polyphenols/groups: **groups get no structure** and stay `UNKNOWN`. RDKit fingerprints/descriptors; `IMAP-` joins with provenance | resolution needs an unlicensed source |
| B05 full process ontology v0 | P2 | Parv → Kush | W1–W3 | — | `PROC-` with families + the escape processes of §B05 (sous-vide, dum, tadka, …), parameters evidenced only | — |
| B06 evidence expansion | K8 | Kush → Parv | W3–W5 | DEL-1 v0 | 12-family anchor matrix; **kinetic-parameter rows** for focused systems (SX-06-04: acrylamide/potato, Maillard glucose/glycine, vitamin C, anthocyanin, chlorophyll) with T/t/pH conditions as reported | source class exhausted (Part AC) |
| B07 10k Silver pilot | K17 + P13 | Kush ↔ Parv | W3 decision; W5 run | **§257P all ticked at W3**, licence for the corpus, **H3** for tokens | Silver v0, card, vocab/process/quantity growth curves, Silver-vs-Gold errors, cost, reannotation rate, scale/repair/stop decision; stages 1k → 5k → 10k with an audit between each | schema unstable; reannotation too high; licence open; cost over budget |
| B08 NER foundation | P14 | Parv → Kush | W2–W4 | RecipeDB3 artefact permission | common scorer; one matched baseline reproduction; split/leakage audit; **oracle-span → graph** test (AW9). RecipeDB3 numbers stay "external" until rerun | permission refused |
| B09 vocabulary growth | P12 | Parv → Kush | W3–W6 | — | `ING-`/`ALIAS-` growth audit; top-unresolved queue | — |
| B10 CQPO | K7 | Kush → Parv | W1–W3 | — | unit map as data, grammar, `ALLOC-`, symbolic quantities | — |
| B15 bounded chain | P15 | Parv → Kush | W5+ | capacity remains | rank-frequency fit (Clauset–Shalizi–Newman) → one Kinouchi reproduction → one null comparison, on the A2 frequency data held locally | any Lane A slip |

## 3. Blocked / deferred register (restart gates)

| Item | Status | Restart gate |
|---|---|---|
| Silver 25k → 60k → 100k (B07) | `BLOCKED_GATE` | the 10k pilot report says "scale"; §257P fully ticked; corpus licence settled; H3 |
| Evidence → 100k tiered rows (B06) | `PARKED_POST_COURSE` | sources genuinely support it; VOI-ranked acquisition (§224) |
| Kinetic models / hybrids / simulators — D8–D11 (B13) | `BLOCKED_GATE` | G15-4 identifiable kinetic fit on a focused dataset; G15-5; G15-10 for synthetic data |
| Rollout / inverse design (SX-13-06/07) | `BLOCKED_GATE` | G15-11 / G15-12 |
| L14 learned conditioning (B12) | `BLOCKED_GATE` | G14 data gates on DEL-1 v1 |
| L12 learned encoders (B04, T3–T9) | `BLOCKED_COMPUTE` | GPU access + §183.B gates (AR3) |
| NER SOTA programme (B08) | `BLOCKED_COMPUTE` / gate | GPU + every AW10 condition |
| L13 representations (B14) | `PARKED_POST_COURSE` | B04-lite + B11 outputs frozen |
| L13E full programme (B15) | `PARKED_POST_COURSE` | historical-corpus licence audit (RS-15-01) |
| Warnings layer (B16, SX-16-11) | `PARKED_POST_COURSE` | evidence + authority sources per warning class |
| FlavorTwin V2 | `BLOCKED_GATE` | G16-FT; static baselines first |
| Deployment + L17 | `PARKED_POST_COURSE` | core gates pass |
| Compiler E0–E14; JEPA J1–J5 | `BLOCKED_EXTERNAL` | source documents provided (X2, X3) |

## 4. Data / API / licence blockers

| Blocker | Affects | Status / action | Fallback |
|---|---|---|---|
| **RecipeDB 3.0 access** | W2 Gold pilot, DEL-3, DEL-5 sessions, Silver source | email W0 (**H1**). Decision **W1 d5** for the pilot, **W2 d5** for DEL-3 | ask the humans: a licence-audited open corpus (research node N21) |
| RecipeDB3 annotations + notebooks permission | DEL-3 upstream parse, B08 | asked in the AS email | DEL-3 runs on oracle events only; B08 waits |
| RecipeDB terms for annotation and derived release | B07, benchmark release | asked in the AS email | Silver stays private, or BLOCKED |
| FlavorDB / FlavorDB2 | crosswalks, `IMAP-` | non-blocking (AH2) | internal `ING-` + PubChem |
| **Phenol-Explorer** | DEL-1 scale | **no documented export; phenol-explorer.eu serves a Wishart-Lab TLS certificate** → ADR in K4: export? → maintainer request → H2 polite crawl | R6 + literature only |
| USDA R6 | DEL-1 | CC0, CSV + data dictionary; row count unknown until download → counted on W1 d1 | — |
| FSSAI allergen authority | DEL-5 feasibility | build the `ALLERGEN-` snapshot (research node N14) | feasibility without allergens is not shipped |
| PubChem PUG-REST | B04-lite | record terms and rate limits in `API-` | — |
| Claude API (pricing, version) | W7 runs, 10k Silver | **H3** with a token estimate; `claude-api` skill at execution | Ollama-only results, labelled as such |
| Cluster details (startup Q3) | Lane B fan-out | `BLOCKED_EXTERNAL` | laptops (AR2 steps 1–2 only) |
| Parv's GitHub ID | repo, H7 | ask at W0 | — |

## 5. Compute placement (Part AR)

| Job | Class | Placement | Gate |
|---|---|---|---|
| validators, ingestion, EDA, D0–D7 fits, retrieval index, unit engine, replay | C0 | **laptops** (M5, 10 cores, 16 GB) | — |
| bootstrap resampling, null Monte Carlo, RDKit descriptors, LightGBM sweeps, kinetic-parameter fitting, MinHash for Silver | C0/C1 | cluster **once details arrive**, via AR2: local test → 1 node → 10-node shard → inspect → full fan-out; idempotent and checkpointed | H3 above threshold |
| source downloads, PDF/table extraction | C2 | laptop, rate-limited, cached | H2 per source |
| development LLM | C4 | Ollama local | — |
| locked ladder runs; 10k Silver annotation | C4 | Claude API | **H3** each |
| learned encoders, NER SOTA | C3 | **no GPU → `BLOCKED_COMPUTE`**; never relabel a CPU result as SOTA (AR3) | — |

## 6. Benchmark target tier

**Target = 320** (80 dev + 240 locked test, 30 per task type), with **104 as the
guaranteed floor** (AH5).

- Authoring starts in W2 for the session-based types (state, next action,
  constraints, diagnosis, recovery) and in W3 for the evidence types (process
  effect, conflict, abstain).
- **Checkpoint W3 d5:** the measured authoring rate on the first 40 items
  decides target vs minimum. The tier is not shrunk later by lowering quality.
- Freeze at W4 d5. The achieved tier is reported.
- Registry fields per item: task type, difficulty, source family,
  ingredient/process family, evidence regime, answer kind, must-abstain, gold
  evidence, constraints.

## 7. Next seven atomic work packages

| # | WP | Owner → reviewer | Task | Done when |
|---|---|---|---|---|
| 1 | WP-01 | **Parv → Kush** | Seed registries:<br>• `scope_registry.csv` — every SSOT item with an AG3 status + restart condition;<br>• `experiments.csv` with the AK1 fields (scope_lane, dependency_ids, priority, owner, reviewer, data requirement, compute class, human requirement, course/paper relevance, status, restart condition);<br>• `gates.csv`.<br>Built from `registry/ssot_ids.csv` + Part P/Z RS bank + SX IDs; E0–E14 and J1–J5 as `BLOCKED_EXTERNAL` | a script asserts all 218 SSOT IDs and all 190 Part P RS IDs appear exactly once; the 80 Part Z questions are deduplicated against them before getting new RS IDs |
| 2 | WP-02 | Parv → Kush | `DECISIONS.md`: D-1 revised to three lanes, D-2…D-6, AH1–AH15 accepted, X1–X3 recorded | both approve |
| 3 | WP-03 | **Kush → Parv** | Edit and send the Part AS email | **H1** — sent |
| 4 | WP-04 | Kush → Parv | Repo + collaborators (**H7**); CI skeleton; `gate.py` stub; move `Project/culinarystate/` in | CI green on an empty check |
| 5 | WP-05 | Kush → Parv | `SNAP-`/`API-` ledger: re-verify the R6 URLs + CC0, Phenol-Explorer access, RecipeDB API docs, PubChem terms, FSSAI allergen source (AH15); download R6 + data dictionary; pin hashes; count non-empty factors | each fact has a timestamped `SNAP-` row; R6 count recorded |
| 6 | WP-06 | Kush → Parv | Evidence schema v1 (AH1 `origin_type` + `source_family_id`; AH2 `ING-` + `UNRESOLVED_EXTERNAL`; RF semantics fields from AM2) + validators + a CI test with a deliberately broken row | the broken row fails CI (SX-00-01) |
| 7 | WP-07 | Parv → Kush | State-engine core: append-only event log, **three identities** (`ING-` / `ENTITY-` / `STATE-`), `trajectory` field, `replay()`, determinism tests on 10 self-written fixture recipes | replay(events) == snapshot on all fixtures |

---

## Appendix — unchanged parts of the previous plan (Δ = corrected)

- **Repository layout and reuse:**
  - `A1/src/normalization/canonicalize.py` → `ING-` normalisation;
  - `A1/src/normalization/state_taxonomy.py` → B05/DEL-3 seeds;
  - `A1/src/ner/llm_extract.py` → Ollama client pattern;
  - `A2/src/random_controls.py` → B03-lite;
  - the `A2/src/validate.py` + `package.py` pattern → `gate.py` + `SNAP-` hashes;
  - `Project/culinarystate/tools/*` → registries.
- **DEL-2 metrics:**
  - MAE/RMSE on retention fraction;
  - IPS-weighted MAE **alongside unweighted** (Δ AM4);
  - **empirical** interval coverage and width (Δ AH4);
  - 2,000-resample grouped bootstrap;
  - H2 decided by a paired CI on the with-vs-without-process difference;
  - D7 promoted only per the AM5 rule.
- **DEL-3 worked fixture** (our own text: melt butter, reserve 1 tbsp, cook garlic in the rest, recombine): the reserved amount stays **1 tbsp volume**; the rest is "50 g minus an unresolved correlated portion" (Δ AN2); an observation override sets `trajectory=OBSERVED_SESSION` and keeps the prediction in the audit log.
- **DEL-4 headline metrics (Δ AO5):**
  - condition-compatible Recall@K;
  - citation precision;
  - UCR;
  - decision-mode F1;
  - constraint-violation rate;
  - AURC;
  - ECE/Brier;
  - conflict recognition;
  - oracle-vs-predicted gap;
  - latency/cost.
- **Decision points:**

  | When | Trigger | Action |
  |---|---|---|
  | W1 d1 | R6 count low and Phenol-Explorer unavailable | ask before narrowing DEL-1 |
  | W1 d5 / W2 d5 | RecipeDB access missing | ask |
  | W3 | §257P fails | Silver `BLOCKED` |
  | W5 | D7 fails G15-9 | no B6 |
  | W6 | B5 not better than B4 on dev | keep the simpler rung |
- **Verification:**
  - `gate.py` checks every acceptance line, is in CI, and runs weekly;
  - `run_all.sh` rebuilds from pinned snapshots;
  - property tests: unit round-trip, no invented grams, replay determinism, UNKNOWN treated as neutral;
  - the benchmark hash is checked before W7;
  - the Part AT weekly report and `STATUS.md`.
