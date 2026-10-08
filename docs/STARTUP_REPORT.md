# Startup report — CulinaryState / Group 17 (MDMA)

**For:** Kush Tokas (2023296) and Parv Goyal (2023374) · **Date:** 6 Oct 2026 ·
**Session:** with Parv (inferred from this machine's account and git identity) ·
**Contract:** master prompt v2.0, Part AF

## Status: B00/B01 pre-work — startup contract items 1–9 done; waiting on you (item 10)

Nothing gated has been touched: no repository, no email, no downloads, no
scraping, no agents spawned, no compute used.

---

## 1. Understanding (Part U, Day 1)

**What we are building.** A cooking assistant that knows what state the food is
in, what a process does under given conditions, and when it does not know —
`CulinaryState-RAG = State + Evidence + Transition + Constraints + Uncertainty + Decision`.
Its scientific base is a **sparse** evidence ledger. Most ingredient × process ×
condition cells have never been measured; the system keeps them UNKNOWN and
abstains rather than inventing chemistry.

**What is binding, and in what order.**

| Rank | Document | What it decides |
|---|---|---|
| 1 | SSOT v15.0 | the laws, gates and definitions — *how* the work is judged |
| 2 | Proposal PDF | the course contract, DEL-1…5 — *what* must ship |
| 4 | Master prompt | procedure: blocks, registries, gates, honesty rules |

**The central tension.** The master prompt describes a multi-year programme:
18 blocks, ~240 research questions, a 60k–100k-recipe Silver corpus, an NER
engine aiming at state of the art, and a ~100-server cluster. The proposal you
submitted is a two-person semester project with five deliverables, no GPU and a
lean Python stack. The SSOT anticipates this gap:

- §279.8 says the next action is to *choose which thread becomes the first
  paper-grade execution*;
- §226.9 says M1–M3 are *sufficient for a coherent student research package*;
- §257K gives a semester-scale checklist.

So the first real decision is the **semester cut** (Q1). Everything below assumes
the recommended default.

**What we already have.** The A1 corpus (11,983 BBC Good Food recipes with
step-level text and a partial per-step parse) and the A2 random-control code.
SSOT §279.3 explicitly says to reuse "A2 null-model code as an M0 seed".

**What "done" means.** Every deliverable has an artifact path, a hash, tests,
metrics with CIs, a gate verdict and the experiment IDs behind it (Part T).
UNKNOWN is better than fabricated completeness.

---

## 2. Done (startup contract items 1–9, with evidence)

| # | Item | Result | Evidence |
|---|---|---|---|
| 1 | Verify the exact SSOT file | **Match.** 1,799,542 bytes, 45,697 lines, 309 top-level headings, current return point §279 | `docs/SSOT_INDEX.md` §1–2; sha256 `1c9262bf…5644` |
| 2 | Build and verify `SSOT_INDEX.md` | **Built; 22/22 inventory checks pass**, one with a documented deviation (below) | `tools/build_ssot_index.py` (deterministic; exit 1 on any undocumented mismatch); `registry/ssot_ids.csv` (218 IDs with every line number) |
| 3 | Verify proposal deliverables | **DEL-1…5 confirmed** against the 3-page PDF; master prompt Part T1 matches except one block mapping (Q1) | `docs/COVERAGE_MAP.md` §1 |
| 4 | Coverage map | SSOT object → block → experiment → gate → deliverable. 19 of 30 RQ16 questions fall inside the course contract | `docs/COVERAGE_MAP.md` |
| 5 | Fill verifiable placeholders | Filled what the machine proves; the rest are questions | §5 below |
| 6 | Questions | 5, each with a default | §4 below |
| 7 | P0 research-spawn DAG | **All 51 P0 questions placed** (asserted in code): wave 1 = 9 nodes, wave 2 = 12, wave 3 = 8 deferred or conditional, 1 routed to you | `research/P0_SPAWN_DAG.md`, `registry/research_spawns.csv` |
| 8 | Two-week plan + compute placement | Day-by-day, owner → reviewer, gate per row; all on dev machines, no GPU | `docs/PLAN_14_DAYS.md` |
| 9 | Acquisition plan + email draft | 13 candidate sources, every licence `[U]`; email ready, **not sent** | `docs/ACQUISITION_PLAN.md`, `registry/datasets.csv`, `docs/email_drafts/` |

## 3. Problems found

| # | Problem | Handling |
|---|---|---|
| P1 | **SSOT §168 has no heading.** Its only subsection, `## 168.1`, is orphaned inside §173 (L10551). Appendix 1's "§0–§279" is therefore slightly wrong about the file. The file itself is the right one: bytes and lines match exactly. | `CR-0001` in `registry/change_requests.md`. The SSOT is not edited (§D5). The indexer accepts this one deviation only because a CR names it. |
| P2 | **PART I has no header.** The SSOT's text calls §0–§127 "PART I", but only PARTs II–XIII have `#` lines. | Optional `CR-0002`. Navigation only. |
| P3 | **Three contract mismatches.** (a) Part T1 maps DEL-3 to B08–B11, but the proposal says DEL-3 "does not re-implement scraping or NER". (b) SSOT §253.1's "minimum strong course deliverable" requires a Deep-Gold benchmark, a Silver pilot and a parser, none of which the proposal promises. (c) RQ16-01/02/05/07/11 assume "Deep Gold" data the proposal never names. | Not resolved silently, per §A3 → **Q1** |
| P4 | **The merged plan is missing.** `CulinaryState_Recipe_Compiler_FINAL_MERGED_PLAN.md` (rank 3 in §A3) is not in `Project/`, so experiments E0–E14 and compiler stages P0–P10 cannot be seeded. | Proceeding without it. Send it if it exists. |
| P5 | **The A1 parse is partial.** `instruction_events.jsonl` has ingredients and utensils per step, but actions, duration, temperature and output state are null for every step. | DEL-3 needs an upstream action parse; research node N7 covers it |

## 4. Decisions needed

Each question has a recommended default, and says what happens if it goes
unanswered.

**Q1 — Semester cut (H8).** *Default:* the submitted proposal is the course
contract. The cut is §279.8 thread 1 (the core CulinaryState-RAG substrate) plus
thread 2 restricted to M1–M2 (DEL-1, DEL-2), with M3 kinetics as the first
stretch. DEL-3 consumes an existing parse and does **not** build NER (B08). The
"Deep Gold" role is filled by DEL-3's 40 recipes and 30 sessions plus DEL-5's
~80 questions. B03 classical replication stays in as a small item, because §128
names it the first code and the A2 code already exists. Deferred until after the
course: B04 molecules, B07 Silver factory, B08 NER, B15 cultural evolution,
FlavorTwin beyond the ≤10-ingredient stretch.
*If unanswered:* I do only research and design, and build nothing that depends on
the cut.

**Q2 — Course calendar.** The dates for proposal phases P1–P5, any mid-review,
and the final submission. Is there a rubric?
*Default:* plan in relative days, as `PLAN_14_DAYS.md` does.
*If unanswered:* I cannot back-schedule DEL-5, which is the crunch risk.

**Q3 — Compute (H3).** The cluster type, node count and specs, storage, access
method, and the budget threshold.
*Default:* everything runs on your laptops, which the proposal says is enough.
The H3 threshold is 2 node-hours, any paid API, or any cluster job.
*If unanswered:* no cluster use, and research node N22 stays blocked.

**Q4 — Repository (H7).** Parv's GitHub ID, the repo name, and the owner.
*Default:* a private repo `culinarystate` under `kushiiitd05`, with Parv as
collaborator. Parv commits as `Parv Goyal <parvgoyal08@gmail.com>` (this
machine's git identity); Kush uses his own identity on his own machine (Part S3).
*If unanswered:* the work stays in local `Project/culinarystate/`, uncommitted.

**Q5 — Email and data (H1 + H2).**
(a) Was an access request already sent with the proposal, and has anything been
granted? Who sends the email?
(b) May the A1 BBC Good Food corpus be DEL-3's development input — kept locally,
with only derived annotations and offsets ever released?
*Default:* (a) the full email, sent by Kush with Parv in cc, after you both edit
it. (b) Yes for local development only; switch the released benchmark to
RecipeDB or an openly-licensed corpus.
*If unanswered:* no email is sent, and DEL-3 waits for an input source.

## 5. Placeholders

| Placeholder | Value | How it was established |
|---|---|---|
| Kush: roll / GitHub | 2023296 / `kushiiitd05` | master prompt; roll matches the proposal PDF |
| Parv: roll | 2023374 | proposal PDF |
| `{{PARV_GITHUB_ID}}` | **open** — Q4 | not on this machine; the GitHub CLI is not logged in |
| Parv git identity | `Parv Goyal <parvgoyal08@gmail.com>` | `git config --global` on this machine |
| Dev machine (Parv) | Apple M5, 10 CPU cores, 16 GB RAM, 8-core GPU, 90 GB free | `sysctl`, `system_profiler`, `df` |
| `{{CLUSTER_TYPE}}`, `{{N_NODES}}`, `{{SPEC}}`, `{{GPU_SPEC}}`, `{{STORAGE}}`, `{{ACCESS_METHOD}}` | **open** — Q3 | cannot be verified from here |
| `{{COMPUTE_BUDGET_THRESHOLD}}` | proposed 2 node-hours — Q3 | a decision, not a fact |
| `{{REPO_NAME}}`, `{{OWNER}}` | proposed `culinarystate` / `kushiiitd05` — Q4 | decisions |

## 6. Next 3 actions (after your go-ahead)

1. Spawn research wave 1 (N0–N8). N3, the DEL-1 sources, is on the critical path.
2. B00 + B01: repo skeleton with CI, and `experiments.csv` seeded from `registry/ssot_ids.csv`.
3. DEL-1 schema v0 with validators, so ingestion can start once N3 and H2 clear.

## 7. Risk and gate status

| Gate | State |
|---|---|
| H1 external communication | Email drafted, **not sent** |
| H2 licences / acquisition | 13 sources listed, **none requested**; A1 reuse → Q5 |
| H3 compute / money | Nothing run; threshold → Q3 |
| H4 schema MAJOR change | none |
| H5 Gold data | none started |
| H6 claims | none made |
| H7 repository | none created → Q4 |
| H8 scope | **semester cut pending → Q1** |

| Top risk | Mitigation already in plan |
|---|---|
| Programme scope swamps the course deliverables | Q1 cut; §226.9 / §257K as the semester frame |
| DEL-1 sources' licences block storage | N1 + N3 run first; "store derived" fallback |
| DEL-3 has no licensed recipe input | Q5; N21 conditional fallback |
| Brief review overloads two people | briefs paired with block owners; wave 3 not started |
