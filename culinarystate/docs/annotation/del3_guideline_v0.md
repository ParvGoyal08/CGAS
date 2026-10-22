# DEL-3 Gold annotation guideline — v0

**Applies to:** the W2 design pilot (20 hard recipes), the course Deep Gold (≥40
recipes, double-annotated) and the 30 scripted sessions.
**Owner:** Parv (P4) · **Reviewer:** Kush · **Status:** v0, to be revised after the pilot.
**Validator:** the WP-07 state engine. A gold file that does not replay is not
accepted.

Background: research brief `research/briefs/RS-07-05.md`. The closest precedent is the
English Recipe Flow Graph corpus (300 recipes, inter-annotator agreement 82.3–90.5 F1).

---

## 1. Independence protocol (non-negotiable)

1. **No LLM pre-fill.** Annotate from the recipe text only. No model output may be
   open while you annotate (v4.0 AH6; SSOT §236–237).
2. **No discussion** of a recipe until both annotators have submitted it.
3. **Validate before submitting:**
   `PYTHONPATH=src python3 -c "from culinarystate.state_graph.gold import load_gold; load_gold('gold/<recipe>.<you>.yaml')"`
4. Log the minutes spent per recipe in the file header (`minutes: 25`). The time
   measured on the first recipes sets the realistic Gold target (AH6).
5. Agreement is computed **before** adjudication (§7).

## 2. Three identities — never collapse them (v4.0 AN1)

| You write | It means | Example |
|---|---|---|
| `concept: butter` | the food concept (becomes `ING-butter`) | butter in general |
| `id: butter_res` | **one physical lot** in this recipe (becomes `ENTITY-<recipe>-butter-res`) | the 1 tbsp set aside |
| — | a **state version** of a lot; the engine creates it (`STATE-…-v2`) | that butter after melting |

Use short lowercase singular concepts (`onion`, `chicken thigh`). Local ids are
yours to choose; agreement does not depend on them.

## 3. Operations — the closed set

One instruction clause is usually one event. "Chop and fry the onion" is two
events: TRANSFORM chop, then TRANSFORM fry.

| Op | Use when | Inputs → outputs |
|---|---|---|
| `CREATE` | an ingredient first enters the recipe (the ingredient list or its first mention) | — → new lots |
| `TRANSFORM` | the same lot changes state: cut, heat, whisk, rest | 1 lot → same lot, new version |
| `MERGE` | ≥2 lots become one new intermediate ("add X to Y", "combine") | ≥2 → 1 new lot |
| `SPLIT` | one lot is divided ("divide into 4", "separate the eggs", "drain") | 1 → ≥2 new lots |
| `RESERVE` | part is set aside for later ("reserve", "save", "set aside") | 1 → **[reserved, rest]**, in that order |
| `RECOMBINE` | a reserved lot rejoins ("add the reserved butter") | ≥2 (≥1 reserved) → 1 new lot |
| `DISCARD` | the text says to discard / throw away | ≥1 → none |
| `TRANSFER` | a lot moves to a vessel or place ("transfer to a bowl", "chill in the fridge") | lots → same lots, `location` set |
| `SET_FIELD` (`plan:`) | a planned state or endpoint (§4) | 1 lot |
| `OBSERVE` (`observe:`) | **sessions only:** what the cook reports seeing | 1 lot |
| `OMITTED_STEP_CANDIDATE` | a step the text implies but never states (§5) | — |

### Decision rules for common phrasings

| Text | Annotate as | Do NOT |
|---|---|---|
| "Add the onions to the oil" | `MERGE [onion, oil]` | treat the oil as a vessel |
| "Add the onions to the pan" (pan is empty) | `TRANSFER onion, location: pan` | invent a pan lot |
| "Add to the pan" (no object) | input = the lot the text refers back to (implicit argument) | leave the input empty |
| "Drain the pasta" | `SPLIT pot → [pasta, cooking water]`; the water lot stays alive | discard the water unless the text says so |
| "Drain and discard the liquid" | `SPLIT` then `DISCARD` the liquid | — |
| "Reserve 100 ml of the water" | `RESERVE water → [reserved {qty 100 ml}, rest]` | compute the rest yourself |
| "Divide the dough in half" | `SPLIT` with `fraction: 0.5` on the first lot and no qty on the last | write "250 g" unless the text does |
| "Season to taste" | `MERGE [dish, salt]`, salt `qty: {raw: to taste}` | give salt a number |
| "Cook until golden, about 8 minutes" | `TRANSFORM cook` + `plan: {colour_endpoint: golden, duration: {value: 8, unit: min}}` | — |
| "over medium heat" | `plan: {heat_level: medium}` | turn it into °C (v4.0 W2 rule 2) |
| "Bake at 180 °C" | `plan: {oven_setpoint: {value: 180, unit: C}}` | call it the food's temperature (W2 rule 1) |

## 4. Quantities and planned fields

- **Copy amounts exactly as written:** `qty: {raw: "2–3 tbsp", unit: tbsp, lo: 2, hi: 3}`.
  `value`, `lo` and `hi` only when the text gives numbers.
- **Never convert units.** The engine keeps "50 g − 1 tbsp" symbolic. You never
  compute grams.
- **Verbal amounts** (`pinch`, `to taste`, `as needed`, `handful`) → `raw` only, plus `unit` if it is a token.
- **Planned fields:** `plan: {field: value}` or `plan: {field: {value: …, unit: …}}`.
  Use these field names consistently in v0: `phase`, `form`, `colour_endpoint`,
  `texture_endpoint`, `aroma_endpoint`, `duration`, `heat_level`, `oven_setpoint`,
  `doneness`. A new name needs a note in the disagreement log.
- `plan:` attaches to the event's result lot: the output of a MERGE/RECOMBINE, or
  the input of a TRANSFORM. On a SPLIT, write a separate `SET_FIELD` event.

## 5. Hidden steps (v4.0 AN4)

**Never insert a step the text does not state.** If one is implied (dried
chickpeas with no soak, a yeast dough with no proof), add:

```yaml
- op: OMITTED_STEP_CANDIDATE
  id: soak-chickpeas
  rationale: "dried legumes are normally soaked before cooking"
  proposes: {op: TRANSFORM, input: chickpeas, process: soak}
```

Adjudication decides whether to `ACCEPT_CANDIDATE` or `REJECT_CANDIDATE`. Candidates
are scored for precision (SX-05-03 / SX-11-04).

## 6. File format

One file per recipe per annotator: `gold/<recipe_id>.<annotator>.yaml`. The
complete worked example is `gold/fixtures/F01.A.yaml`. Required keys:

```yaml
gold_format: DEL3-GOLD-v0
recipe_id: <RecipeDB Recipe_ID>
annotator: <initials>
guideline_version: v0
minutes: <int>
steps:
  - step: 1
    text: <the instruction sentence, copied>
    events: [ … ]
```

Process verbs go in `process:` as written. They are resolved against the B05
vocabulary (`ledgers/process/`). An unknown verb is kept raw, so do not invent a
synonym.

## 7. Agreement and adjudication

Run: `PYTHONPATH=src python3 tools/del3_agreement.py gold/<r>.A.yaml gold/<r>.B.yaml`

| Metric | What it compares |
|---|---|
| event F1 | (step, op, process, inputs) |
| edge F1 | every relation edge |
| **merge/split F1** | MERGES_INTO, SPLITS_INTO, RESERVED_AS, RECOMBINED_WITH, DISCARDED_FROM |
| quantity agreement | stated amounts of created lots |
| allocation agreement | derived quantities (the order of a sum does not matter) |
| field agreement | final planned/observed fields |

- **Lots are matched by derivation, not by your ids.** For example,
  `MERGE:cook(RESERVE:reserve(butter).rest, garlic)` is the same lot whatever
  each annotator called it.
- **Known property — cascade:** a missed reserve or split changes every lot
  derived from it. That is semantically right (the dish is composed differently),
  but one root error can zero merge/split F1. The CLI lists the root edge first in
  `a_only`/`b_only`. Fix roots first.
- **Proposed gate** (to be confirmed with Kush): over the 20-recipe pilot, mean
  merge/split F1 ≥ 0.80 before Deep Gold starts. Otherwise revise this guideline
  and re-annotate the disagreeing recipes.
- **Adjudication:** both annotators review the disagreement listing together and
  produce `gold/<r>.ADJ.yaml`. Every rule clarified goes into the changelog below
  with a version bump.

## 8. Hard strata to include in the pilot (v4.0 AW6)

Each of the 20 pilot recipes should contain at least one of these, and each
stratum should appear at least twice:
- ranges or fractions;
- verbal quantities;
- count/container units;
- reserve/split/recombine;
- discard;
- implicit arguments ("it", "the mixture", "the rest");
- multiple actions per sentence;
- "until …" endpoints;
- nested intermediates;
- optional/"or" alternatives (v0: annotate the first alternative and add `note: alternative …`);
- an implied hidden step.

## 9. Scripted sessions (30)

A session is a recipe gold file plus `OBSERVE` events placed where the scripted
cook reports a state ("the onions are still pale"). Each observation must be
checkable against the final replayed state. The engine keeps the overridden
plan/prediction in the audit trail, so the scoring can test override behaviour
(RQ16-15). The session format is otherwise identical.

## Changelog

| Version | Date | Change |
|---|---|---|
| v0 | 2026-10-07 | first version; F01 worked example A/B/C; agreement tool |
