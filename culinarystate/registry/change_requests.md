# SSOT change requests

Master prompt §D5: changes to the SSOT are proposed here and applied only after
human approval, as a new `v15.x` file with a merge-register entry (SSOT §139).
**The SSOT itself is never edited in place.**

| ID | Status | Severity | Raised |
|---|---|---|---|
| CR-0001 | PROPOSED | PATCH | 2026-10-06, startup verification |
| CR-0002 | PROPOSED (optional) | PATCH | 2026-10-06, startup verification |

---

## CR-0001 — §168 has no heading; `168.1` is orphaned inside §173

| Field | Value |
|---|---|
| § affected | §168 (missing), §173 (L10524–10583) |
| Found by | `tools/build_ssot_index.py`, check "Numbered sections §0–§279 all present" |
| Current text | No `# 168.` heading exists anywhere in the file. `## 168.1 Immediate next learning block` is at **L10551**, inside `# 173. LEGACY v7 RETURN POINT — SUPERSEDED BY §172` (L10524). |
| Evidence | §167 is at L10325 and §169 at L10356, with no §168 between them. Searching for any heading of any level starting `168` returns only L10551. File identity matches Appendix 1 exactly (1,799,542 bytes, 45,697 lines), so this is a defect in the file as delivered, not a changed file. |
| Likely cause (**inference, not verified**) | §173 is the *legacy v7* return point. In v7 it was probably numbered §168, and its subsection kept the old number when the section was renumbered. |
| Proposed text | **Option A (recommended):** renumber `## 168.1` → `## 173.1`, since it sits inside §173. **Option B:** restore a `# 168.` heading if the history shows it existed. |
| Impact on IDs/gates | None. No RQ/E/G ID lives in L10524–10583. The only cross-reference to §168 anywhere is the orphaned heading itself. |
| Also fix | Master prompt Appendix 1 says "Numbered sections §0–§279"; it should read "§0–§279 except §168" until this CR lands. |

## CR-0002 — PART I has no header (optional)

| Field | Value |
|---|---|
| § affected | §0–§127 (L1–L7856) |
| Current text | The file has `# PART II` … `# PART XIII` headers but no `# PART I`. The SSOT's own text calls §0–§127 "PART I" (e.g. L9102: "written back into PART I rather than living only in PART III"). |
| Proposed text | Insert `# PART I — v1–v3 FOUNDATIONS` (wording for the humans to choose) immediately before `# 0. READ THIS FIRST` at L226. |
| Impact | Navigation only. **Note:** adding a line shifts every line number after L226, so `docs/SSOT_INDEX.md` must be rebuilt in the same change, and the top-level heading count becomes 310. |

## CR-0003 — master plan v4.0: RecipeDB3 NER description (DEC-040)

| Field | Content |
|---|---|
| Document | `Plan_SSOT15_v4_0.md` |
| § affected | L392 (Part AW "external numbers") and L701 (B08 hybrid tagger) |
| Current text | "CoSyLab **RecipeDB3** …: DeBERTa ingredient macro-F1 0.9557; spaCy instruction micro-F1 0.9258 / macro 0.8698"; and "fine-tuned encoder (DeBERTa/RoBERTa ± CRF)" |
| Proposed text | Keep the numbers and add: "SOURCE_REPORTED under the released notebook protocol: `microsoft/deberta-base` (v1, no CRF); best model selected on the test split; SIZE mapped to O; repository unlicensed — written permission required. Our matched and leakage-safe reproductions: `experiments/B08/recipedb3_repro/`." |
| Impact | Wording and provenance only. No change to scope |
