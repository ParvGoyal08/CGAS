# First two weeks — execution plan and compute placement

Startup-contract item 8 (master prompt Part AF). This adapts Part U to the
**recommended semester cut** (Q1 in `STARTUP_REPORT.md`). Days are counted from
**Day 1 = the day the humans approve**, because the course calendar is not yet
known (Q2). Owners follow the Part S2 split; every item has a reviewer from the
other person.

**Nothing below has started.** Rows marked with a gate cannot begin until that
gate is approved.

## Day by day

| Day | Owner → reviewer | Work | Output | Gate / exit check |
|---|---|---|---|---|
| 0 | Claude | Startup package (this folder) | `docs/*`, `registry/*`, `research/P0_SPAWN_DAG.md` | Humans answer Q1–Q5 |
| 1 | Kush → Parv | **B00** repo skeleton (Part S layout), CI: lint + unit + data-validation; local experiment tracking | private repo, green CI | **H7** repo creation |
| 1–2 | Parv → Kush | **B01** seed `experiments.csv` with every SSOT ID from `registry/ssot_ids.csv`; `gates.csv`; dependency DAG | registries | SX-01-01: index counts match Appendix 1 (already PASS, with CR-0001) |
| 1–3 | Claude (agents) | **Research wave 1**: N0–N8 in parallel | 9 briefs | Each brief reviewed by its block owner |
| 2 | Kush → Parv | **B02** §42 API-audit sheet; send the Bagler email | email sent; `API-` ledger stub | **H1** before sending |
| 2–4 | Kush → Parv | **DEL-1 schema v0**: minimal `EVD-`/`COND-`/`SVAR-`/`STUDY-`/`MEAS-` subset carrying exactly the proposal's DEL-1 fields; Pydantic validators; property tests | `ledgers/schemas/`, tests | CI rejects a deliberately broken row (SX-00-01) |
| 2–4 | Parv → Kush | **B05** process ontology v0 — only the process IDs DEL-1 and DEL-3 need, plus an explicit `UNMAPPED` that keeps the raw verb | `PROC-` v0 | Coverage report on DEL-1 source processes |
| 3–5 | Claude (agents) | **Research wave 2**: N9–N20 as parents clear | 12 briefs | Reviewed |
| 3–6 | Kush → Parv | **DEL-1 ingestion**: USDA R6 retention factors + Phenol-Explorer 3.0 processing data | ≥1,000 rows, every one carrying source + tier + condition status + censoring flag | **H2** per source, from brief N3 |
| 4–6 | Parv → Kush | **B03** first code: port the A2 random-control generator as the M0 null; Level-7 `n_ij`, `N_s` with tests | `src/…/classical/` | SX-03-01-lite. SSOT §128 makes L7/L8 the first code; §279.3 says to reuse the A2 code |
| 5–8 | Parv → Kush | **DEL-3 spec**: state-graph schema (merge / split / reserve / recombine, observation override, provenance per field); gold annotation guideline v0 | `docs/adr/0001-state-graph.md`, guideline | Represents 10 hard recipes without schema improvisation (§252 Phase-0 exit) |
| 6–9 | Kush → Parv | **B10** quantity grammar + unit map v0 (as data, with sources and intervals) | `UNIT-` map, parser | SX-10-02 **invented-grams audit = 0** |
| 7–10 | Kush + Parv | **DEL-3 gold pilot**: 20 recipes, annotated independently by both, **no LLM pre-fill** | agreement report | Agreement measured (Part U Day 8–12) |
| 8–12 | Kush → Parv | **DEL-1 literature rows**: first curation cells of §144.3 (rice, potato, broccoli, garlic, beef, wheat dough, cabbage). LLM extraction + human verification against the source span | ≥40 verified rows | G15-H: every row verified against its cited span |
| 10–13 | Parv → Kush | **DEL-2 M1**: observation-mask audit, density/MNAR profile; freeze pair-holdout, ingredient-disjoint and study-disjoint splits; write experiment cards A–I and K–U **before** touching held-out data | cards, frozen splits | Part Q1 pre-registration committed |
| 12–14 | Kush → Parv | DEL-1 v1 freeze + data card + Part M audit | ledger v1, `eda/…/report.html` | G14-1, G14-2, G15-1 |
| 14 | both | Review; confirm or revise the semester cut | decision record | **H8** |

## Balance check (Part S2)

| | Kush | Parv |
|---|---|---|
| Blocks led in these 14 days | B00, B02, B06/DEL-1, B10 | B01, B03, B05, B11/DEL-3 spec, B13/DEL-2 |
| Shared | DEL-3 gold pilot | DEL-3 gold pilot |

Parv leads more blocks; Kush's DEL-1 ingestion and literature curation are the
heaviest single items. If it turns out unbalanced in practice, move B05 to Kush.

## Compute placement (Part R2)

**Cluster details are unknown (Q3)**, so nothing is placed on it. The proposal
itself says DEL-1…5 need **no GPU** (proposal §8).

| Job class | This fortnight's jobs | Placement |
|---|---|---|
| C0 CPU-light | validators, ingestion, EDA, M0 null Monte Carlo, unit engine, split building | Parv's dev machine: Apple M5, 10 CPU cores, 16 GB RAM, 90 GB free (verified locally); a matching setup on Kush's machine |
| C1 CPU-heavy | none planned | — |
| C2 I/O | USDA R6 and Phenol-Explorer downloads; DOI fetches for literature rows | dev machine, polite and cached, after H2 |
| C3 GPU | none needed | — |
| C4 LLM | research briefs; literature extraction (always human-verified) | Claude Max session; prompts and versions logged |

**H3 default threshold (proposed):** any job over 2 node-hours, any paid API, or
any cluster job needs approval. This replaces `{{COMPUTE_BUDGET_THRESHOLD}}` once
the humans confirm it.
