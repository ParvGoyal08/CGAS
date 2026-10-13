# GOLD_ANNOTATION_GUIDE — DEL-3 gold recipes and sessions

| Part | Location |
|---|---|
| Format | DEL3-GOLD-v0 YAML; schema in `docs/annotation/gold_schema.json`; rules in `docs/annotation/del3_guideline_v0.md` |
| Per-recipe checklist | `docs/annotation/annotation_checklist.md` |
| Patterns | `gold/hard_examples/` (8 hard cases); `gold/UNKNOWN_examples/` (4 cases where UNKNOWN is correct); `gold/hard_examples/invalid/` (3 structures the validator rejects) |
| Validate | `.venv/bin/python tools/validate_gold.py gold/<file>.yaml` |
| Agreement | `.venv/bin/python tools/del3_agreement.py gold/<r>.A.yaml gold/<r>.B.yaml` (event / edge / merge-split F1, quantity and field agreement) |
| Adjudication | `docs/annotation/adjudication_template.md` + `adjudication_template.csv` |

**Plan:**
- 40 RecipeDB recipes, stratified by cuisine and length;
- 10 of them double-annotated by Parv and Kush, independently, before adjudication;
- 30 scripted sessions: a recipe plus cook reports as OBSERVE events, such as "the onions are still pale".

**The agreement gate** (DEC-018, proposed): mean merge/split F1 ≥ 0.80 on the double-annotated set before the rest is annotated. If it fails, fix the guideline first.

`FIX-` recipes are examples only and never enter the benchmark.
