# EVIDENCE_REVIEW_GUIDE — verifying literature cells (D1)

The full rules are in `docs/annotation/literature_verification_v0.md`; this is the working version.

1. Open `ledgers/literature/verification_queue_ranked_v1.csv`. Filter `queue_category == VERIFY_NOW`. Work top-down, mixing families. HTML overview: `eda/literature/evidence_precheck_report.html`.
2. For each row, open `paper_url`. Find the `table`, the `row_header` and the `col_header`.
3. Check that `cell_verbatim` is exactly the number in the paper. If the row is a processed value, also check `raw_counterpart_verbatim`.
4. Check the AI fields: `ai_food`, `ai_process_ids` (and conditions), `ai_target`, `ai_unit`, `ai_value_kind`, plus the table's basis and retention method. Read `ai_quote` against the paper.
5. If everything is right, set:
   - `is_retention_relevant = yes`;
   - `verifier = <your name>`;
   - `verified_utc = <ISO time>`.

   If something is wrong, write the correct value in a `final_*` column (`final_ingredient_id`, `final_process_ids`, `final_target`, `final_unit`, `final_value_kind`, `final_tier`, `final_conditions`) and then sign.
6. If the cell is not a valid process effect, set `is_retention_relevant = no` and give the reason in `human_notes`.
7. Never type a number. Never sign a row you did not check against the paper.
8. Run `.venv/bin/python tools/promote_literature.py`. Fix anything in `ledgers/evidence/literature_v1.rejects.csv`, usually an unmapped process.

**Target:**
- ≥ 40 signed rows across ≥ 6 families;
- include a few kinetics rows (rate constants) and raw-vs-cooked pairs.
