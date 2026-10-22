# Coverage map — SSOT object → Block → experiments → gate → deliverable

Startup-contract item 4 (master prompt Part AF). Built against SSOT v15.0
(`sha256 1c9262bf…`, see `docs/SSOT_INDEX.md`) and the submitted proposal PDF
`Group17_MDMA_Mini_Project_Proposal_Brief.pdf` (3 pages, created 1 Oct 2026).

**Status: PROPOSED.** The RQ16 mapping comes from reading each §247 question body
(question, data required, baseline), not from titles alone. Block assignment
becomes binding only after the humans approve the B01 portfolio and the semester
cut (H8).

---

## 1. Course contract view — what must be delivered

Acceptance text in the right-hand column is **from the proposal PDF** (rank 2 in
§A3). Where the master prompt's Part T1 differs, the difference is called out.

| DEL | Blocks | SSOT anchors | Experiments | Gates | Acceptance (proposal PDF) |
|---|---|---|---|---|---|
| **DEL-1** Process-Effect Evidence Ledger + data card | B02, B06 (+B05 process names, B09 name normalisation) | §144.2–144.3, PART IX §§197–205 (§203 evidence ledger), §216 data contracts, §239.1 rules, §226.3 M1 | SX-02-01/02/03, SX-06-02 retention ingestion, SX-06-03 raw-vs-cooked, SX-06-08 LLM-extraction accuracy | G14-1, G14-2, G15-1, G15-H, G16-PROV | ≥1,000 rows from public retention DBs (Phenol-Explorer, USDA) + ≥40 hand-verified literature rows; fields incl. condition status, tier, DOI, censoring flag; names normalised to RecipeDB/FlavorDB; every row has source + tier; coverage and bias report |
| **DEL-2** Sparsity-aware completion + cold-split benchmark | B13 | PART XI §§219–227, esp. §226.3–226.4 (M1–M2); §226.9 names M1–M3 as a sufficient student package | SX-13-01 baselines, SX-13-03 completion, SX-13-04 MNAR evaluation | G14-4/5/6, G15-2, G15-3, G15-6, G15-7, G15-9, G15-R | Density + MNAR profile; pair-holdout, ingredient-disjoint, study-disjoint splits; persistence / process-mean / nearest-evidence / LightGBM vs biased MF / FM with side info; propensity-weighted eval; split-conformal intervals; answers **H2** with study-level bootstrap CIs; negative results reported |
| **DEL-3** Event-sourced state-tracking engine | B11 (+B10 for reserve/split quantities) | §233, §107 hidden steps, §257P graph checklist | SX-11-01, SX-11-03, SX-11-05; E16-D; RQ16-14, RQ16-15, RQ16-24 | G16-GRAPH | Typed ops merge / split / reserve / recombine; belief-state fields with provenance; direct-observation override; **consumes structured recipe tables / upstream parser output; does not re-implement scraping or NER**; 40 gold recipes + 30 scripted sessions; state-field accuracy, replay consistency, merge/split F1 |
| **DEL-4** Evidence-aware retrieval + calibrated abstention | B16 (RAG core) | §241, §242, §257O | E16-E, E16-F, E16-G; RQ16-02/03/04/05/06/21/22 | G16-EVID, G16-CONFLICT, G16-CAL, G16-OOD, G16-PROV | Hybrid structured + BM25 + dense over the ledger; condition compatibility ("unknown is not a mismatch"); 7 evidence classes; confidence vector; answer / ask / abstain; condition-compatible Recall@K, risk–coverage, unsupported-claim rate, ECE |
| **DEL-5** End-to-end CulinaryState-RAG + benchmark + demo | B16, B17 | §243, §245, §253.7 | E16-H, E16-I, E16-J, E16-L; RQ16-01/16/17/18/19/20/28/29/30 | G16-DEC, G16-REC, G16-TRANS, §257P final-claims list | Relevance gate, feasibility filter, diagnosis + recovery with Pareto trade-offs; ~80 questions × 8 task types; ladder B0 LLM-only → B5 + evidence routing/abstention; one-at-a-time ablations; oracle-upstream tests; small chef/peer review; 8-scenario Streamlit demo |
| Stretch | B14, B16 | §246 | E16-K; RQ16-25 | G16-FT | Process-conditioned FlavorTwin slice for ≤10 anchor ingredients |

**Proposal hypotheses → where they are tested**

| Proposal | Tested by | Decided at |
|---|---|---|
| H1 state-aware retrieval beats text-only / dense RAG | RQ16-01, RQ16-14 → B4 vs B1/B2 in DEL-5 | E16-L |
| H2 process info beats identity-only on unseen pairs and studies | DEL-2 pair-holdout + study-disjoint | G15-3, G14-5, G14-6 |
| H3 evidence routing + abstention lowers unsupported claims at small coverage cost | RQ16-05, RQ16-06 → B5 vs B4 | G16-CAL, G15-7 |
| H4 feasibility + recovery respect constraints better than a generic chatbot | RQ16-16, RQ16-18, RQ16-19 | G16-DEC, G16-REC |

### Three contract mismatches found (not resolved — raised as Q1)

1. **Master prompt T1 maps DEL-3 to B08–B11.** B08 is the NER engine. The proposal
   says DEL-3 "does not re-implement scraping or NER". Under the precedence rule
   (§A3: proposal rank 2 > master prompt rank 4) the proposal governs; DEL-3 needs
   only B11 (+B10), fed by an existing parse.
2. **SSOT §253.1 "minimum strong course deliverable"** lists a Deep-Gold benchmark,
   a Silver pilot and a semantic parser. None of these appear in the submitted
   proposal. §A3 says a contract/SSOT disagreement must be raised, never
   silently resolved.
3. **"Deep Gold" in RQ16-01/02/05/07/11.** Under the proposal, its role is played by
   DEL-3's 40 gold recipes + 30 sessions and DEL-5's ~80-question benchmark. That
   substitution should be explicit, since G16-CAL requires "held-out independent
   gold".

---

## 2. SSOT registry view — every RQ16 and E16

`Course` = inside DEL-1…5. `Program` = SSOT program work outside the submitted
contract; it proceeds only after an H8 scope decision.

| RQ16 | Topic (from §247 body) | Block | E16 | Scope |
|---|---|---|---|---|
| 01 | State reconstruction vs text-only RAG | B11, B16 | E16-L | Course — DEL-5 (H1) |
| 02 | Structured vs dense retrieval, citation correctness | B16 | E16-E | Course — DEL-4 |
| 03 | Condition-aware compatibility reranker | B16 | E16-E | Course — DEL-4 |
| 04 | Semantic evidence packet vs raw chunks | B16 | E16-F | Course — DEL-4 |
| 05 | Calibrated confidence vector vs LLM self-confidence | B16 | E16-G | Course — DEL-4 (H3) |
| 06 | DIRECT→…→ABSTAIN sufficiency policy | B16 | E16-G | Course — DEL-4 (H3) |
| 07 | Quantity grounding (CQPO) vs raw/unit-only | B10 | E16-B | Program; v0 grammar used by DEL-3 |
| 08 | Canonical vocabulary vs string vocabularies (100k aliases) | B09 | E16-C | Program; DEL-1 needs only a name map |
| 09 | Silver utility at 10k–100k | B07 | E16-A | Program |
| 10 | Active learning for Gold-Light | B07 | E16-A | Program |
| 11 | Claude multi-pass vs one-shot annotation | B07, B08 | E16-A | Program |
| 12 | Deterministic validators' catch rate | B07 | E16-A | Program; validator pattern reused in DEL-1 |
| 13 | Duplicate/source leakage inflation | B07 | E16-A | Program; grouping-before-split reused in DEL-2 |
| 14 | Event-sourced session memory | B11 | E16-D | Course — DEL-3 |
| 15 | Direct-observation override | B11 | E16-D | Course — DEL-3 |
| 16 | Feasibility filter | B16 | E16-H | Course — DEL-5 (H4) |
| 17 | VOI clarification | B16 | E16-H | Course — DEL-5 ("ask") |
| 18 | Diagnosis verifier | B16 | E16-I | Course — DEL-5 (H4) |
| 19 | Recovery evidence separate from cause | B16 | E16-I | Course — DEL-5 (H4) |
| 20 | Level-15 transition fallback | B13, B16 | E16-J | Course — DEL-2 → DEL-5, gated by G16-TRANS |
| 21 | Visible completion/evidence class | B13, B16 | E16-J | Course — DEL-2/DEL-4 |
| 22 | Condition-aware conflict handling | B16 | E16-E/F | Course — DEL-4 |
| 23 | Learned quantity encoder downstream | B10 | — | Program |
| 24 | Explicit recipe graph vs flat text | B11 | E16-D | Course — DEL-3 |
| 25 | FlavorTwin process conditioning | B14, B16 | E16-K | Stretch |
| 26 | FlavorTwin recipe context | B14 | E16-K | Program |
| 27 | Human sensory boundary | B16 | — | Program (DEL-5 peer review is not a sensory study) |
| 28 | Source/domain generalisation | B17 | E16-L | Course — DEL-2/DEL-5 splits |
| 29 | Long-tail equity | B17 | — | Course — DEL-5 per-frequency error analysis |
| 30 | Full-system contribution, B0–B5 vs B7 | B17 | E16-L | Course — DEL-5 |

**Count:** 19 of 30 RQ16 questions sit inside the course contract (01–06, 14–22,
24, 28–30), 1 is stretch (25), 10 are program-level (07–13, 23, 26, 27).

## 3. Gate families → deliverables

| Gate family | Count | Course-relevant members | Program-only |
|---|---|---|---|
| G14 (§202, L17078) | 12 | All 12, in reduced form: 1–2 via DEL-1 (schema, dataset card); 3–12 via DEL-2 (held-out labels, baselines, pair-holdout, study-disjoint, condition vs label-only, missingness robustness, calibration, evidence-quality strata, multi-seed CIs for MF/FM, decision record) | — |
| G15 (§215, L22382) | 18 | 1, 2, 3, 6, 7, 8, 9, R, H, I | 4, 5 (kinetic fitting — not committed by the proposal), 10, 11, 12, HYB, INV, RXN |
| G16 (§249.1, L27446) | 14 | EVID, CONFLICT, CAL, OOD, PROV, GRAPH, DEC, REC, TRANS | DATA, VOCAB, QTY, SEM (Silver/NER factory); FT (stretch) |
| G13 (§193.8) | 5 | — | B14 recipe/cuisine representation |
| G13E (§278.5) | 15 | — | B15 cultural evolution (parallel track, §279.5) |

## 4. Program-level families outside the course contract

| SSOT family | Block | Status under the recommended cut |
|---|---|---|
| Level-12 threads T0–T9 (§176), SX-04-* | B04 | Program. DEL-1 only needs ingredient names normalised to FlavorDB, not molecule encoders |
| Classical replication L7–L11, SX-03-* | B03 | **Recommended in-cut as a small item.** §128 names L7/L8 replication as the SSOT's first code, and §279.3 says to reuse the A2 null-model code as the M0 seed, which already exists |
| Process ontology, SX-05-* | B05 | v0 only, as far as DEL-1/DEL-3 need process IDs |
| Recipe corpus factory, SX-07-* / NER, SX-08-* | B07, B08 | Program; deferred |
| Transition ladder D0–D11 (§208–216) | B13 | D0–D6 baselines in-cut (DEL-2, G15-2); D7+ only via G15-9 |
| Sparsity milestones M1–M6 (§226) | B13 | **M1–M2 in-cut** (DEL-1 ledger + mask audit; DEL-2 completion/MNAR/conformal). **M3 partial:** kinetic literature rows (DEL-1) and Arrhenius/thermal-exposure features (DEL-2, proposal §6) are in; identifiable kinetic fitting (G15-4/5) is not promised by the proposal. §226.9 calls M1–M3 sufficient for a student package, so M3 kinetics is the natural first stretch. M4–M6 program |
| L13E: RQ13E-01…22, E13E-01…18, RISK-E1…E12 | B15 | Program; parallel, must not delay the core (§279.5) |
| Epics A–M (§256) | all | Seeded into `experiments.csv` at B01; scoped by the cut |
| Merged-plan E0–E14, P0–P10 | — | **Not provided.** `CulinaryState_Recipe_Compiler_FINAL_MERGED_PLAN.md` (rank 3 in §A3) is absent from `Project/`, so these IDs cannot be seeded |
