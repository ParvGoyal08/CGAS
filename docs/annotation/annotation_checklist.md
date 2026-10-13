# Annotation checklist: one recipe (DEL3-GOLD-v0)

Work top to bottom, ticking each line. Format and rules: `docs/annotation/del3_guideline_v0.md`. Worked patterns: `gold/hard_examples/`, `gold/UNKNOWN_examples/`.

**Before you start**
- [ ] `recipe_id` is the RecipeDB Recipe_ID, never `FIX-…` (fixtures never enter the benchmark).
- [ ] `annotator` = your initials; `guideline_version` = v1.
- [ ] You have **not** looked at the other annotator's file.

**Each step**
- [ ] Copy the step's `text` verbatim.
- [ ] CREATE every ingredient the first time it appears, with `concept` and `qty.raw` verbatim.
- [ ] Quantity: give `unit` plus `value`, or `lo`/`hi` for a range. Never a midpoint. Never grams unless grams are written.
- [ ] Size, form and state go in `plan` (e.g. `form: chopped`), and only when written.
- [ ] Choose the operation:

  | Text says | Operation |
  |---|---|
  | combine | MERGE |
  | divide | SPLIT (fractions only if stated: "equal", "half") |
  | keep back | RESERVE |
  | throw away | DISCARD |
  | add back | RECOMBINE |
  | move | TRANSFER (same lot) |
  | change | TRANSFORM |

- [ ] `process`: the verb **as written**. If the text says "grill or pan-fry", keep the "or"; never pick one.
- [ ] Tool, medium, time and temperature: record only what is written. Otherwise leave it out (it stays UNKNOWN).
- [ ] Endpoints ("until golden") go in `plan`, never as a time.
- [ ] Pronouns and "the mixture": point the event at the correct earlier lot (coreference). Add `span` for the phrase.
- [ ] Optional ingredients: CREATE them with `plan: {optional: true}`.

**Session files** (scripted sessions only)
- [ ] The cook's reports are OBSERVE events with a `span`. They never edit the plan.

**Before you save**
- [ ] `.venv/bin/python tools/validate_gold.py gold/<file>.yaml` → `OK pass`.
- [ ] No number appears that is not in the text.
- [ ] Time spent: ____ min. Doubts are noted at the top as `# DOUBT:` comments; the adjudicator reads them.
