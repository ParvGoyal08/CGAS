# Adjudication record — recipe `<recipe_id>`

**Annotators:** A = ___ · B = ___ · **Adjudicator:** ___ (not A or B) · **Date:** ___

**1. Agreement before adjudication.** Run:

```
.venv/bin/python tools/del3_agreement.py gold/<r>.A.yaml gold/<r>.B.yaml
```

Paste the event F1, edge F1, merge/split F1, quantity agreement and field agreement.

**2. Disagreements.** Record every one. Write one row per disagreement in `gold/adjudication/<recipe_id>.csv`, using the header of `adjudication_template.csv`.

| Category | Meaning |
|---|---|
| OP | different operation |
| LOT | different lot identity / coreference |
| QTY | quantity or unit |
| FIELD | plan/observe field |
| PROC | process verb mapping |
| SPLIT | fractions |
| MISSING | event missing in one file |
| GUIDELINE_GAP | the guideline does not decide the case |

**3. Resolution.** For each row, record the decision (A, B, or NEW) and the guideline section that decides it. A `GUIDELINE_GAP` produces a guideline change proposal. The guideline is never changed silently.

**4. Final file.** Write `gold/<recipe_id>.ADJ.yaml` and run `tools/validate_gold.py` → `OK pass`. The pre-adjudication agreement numbers are what gets reported. They are never recomputed against the adjudicated file.
