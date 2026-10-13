# AI pre-check prompt (literature table cells) — reusable

Give this prompt to an LLM agent with local file access (it was used for the 35-paper pre-check on 2026-10-08/09).
Fill in `{{PMCIDS}}`, `{{CANDIDATES_FILE}}` (candidates_v1.csv or candidates_r2.csv) and `{{OUT_DIR}}`
(ledgers/literature/ai_precheck_v1new/ or ai_precheck_r2/). One agent per 5–9 papers.

---
You are doing an AI PRE-CHECK (not human verification) of literature table cells for a food-science evidence
ledger. LOCAL files only; no network. Create only files in {{OUT_DIR}}; modify nothing else; no git.

Project root: the culinarystate folder (Python: .venv/bin/python, pandas).
Inputs: {{CANDIDATES_FILE}} (one row per verbatim table cell: cand_id, pmcid, table, row_index, row_header,
grid_col, col_header, cell_verbatim, parsed_value, parsed_sd, cell_flags); data/raw/literature/<PMCID>.xml (JATS);
ledgers/process/proc_v0.csv (PROC ids — use existing ids or PROC-UNMAPPED:<verb>);
docs/annotation/literature_verification_v0.md (the human guideline). Papers: {{PMCIDS}}.

For each paper: read Methods (foods, treatments and their STATED conditions, raw vs processed sampling, wet/dry
basis, cooking yield measured or not, replicates, units). For each table decide PROCESS_EFFECT_TABLE vs
NOT_PROCESS_EFFECT. Write one table record per table, and one cell record for EVERY cell of a PROCESS_EFFECT table:

table: {"type":"table","pmcid","table","verdict","reason","foods","treatments","methods_quote","basis","basis_quote",
        "retention_method","retention_quote","units","replicates"}
cell:  {"type":"cell","cand_id","pmcid","table","ai_relevant":"yes|no","ai_role":"RETENTION_REPORTED|PROCESSED_VALUE|
        RAW_REFERENCE|STAT_OR_SD|OTHER|EXTRACT_ERROR","ai_food","ai_ingredient_id":"ING-<slug>","ai_process_text",
        "ai_process_ids":"PROC-a;PROC-b","ai_conditions":"T=..C(MEASURED); t=..min(MEASURED); medium=..(QUALITATIVE)",
        "ai_target","ai_value_kind","ai_unit","ai_raw_counterpart_cand_id","ai_flags":[...],"ai_confidence":"high|medium|low",
        "ai_quote":"<VERBATIM <=200 chars>","ai_model":"<model id>","provenance":"AI_PRECHECK"}

Conventions: raw/control cells → ai_relevant "no", role RAW_REFERENCE; processed cells point to them; physical/texture
properties → "no" + flag non_analyte_property; no raw/untreated reference in the table → "no" + no_raw_reference_in_table;
secondary/cited-study rows → flag review_aggregate_cited_study; SE vs SD → flag SE_not_SD.
HARD RULES: never write/compute/alter a number; quotes must be verbatim substrings of the whitespace-normalised XML
(check with a script); never guess conditions; never fill human columns.
Then run: .venv/bin/python tools/rank_literature_queue.py   (extend its input list if you used a new OUT_DIR).
