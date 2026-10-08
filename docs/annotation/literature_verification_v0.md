# Literature candidate verification — guideline v0 (K8, DEL-1)

**Who:** a human verifier (Parv or Kush). The machine never fills these fields.
**Input:** `ledgers/literature/candidates_v0.csv`. Each row is one table cell, copied verbatim
from an open-access paper (CC BY / CC BY-SA / CC0) by `tools/fetch_literature_candidates.py`.
**Output:** the same row with the verifier columns filled in. Rows marked
`is_retention_relevant=yes` are later promoted by a script into `EvidenceRow`s (tier E2 or E4,
`verification=HUMAN_VERIFIED`). Every other row stays E5 and is never evaluable.
**Target:** ≥ 40 verified rows (proposal DEL-1), stretch 100–150, spread over the 12 anchor
families (v4.0 AI5). Do not take 40 rows from one paper.

## Procedure (per paper, then per cell)

1. **Open the paper.** Use `https://europepmc.org/article/PMC/<pmcid>`, or the raw XML
   in `data/raw/literature/<pmcid>.xml`. Read the **Methods**. Note these six things:
   - the cooking conditions (T, t, medium, water use);
   - raw versus cooked sampling;
   - wet or dry basis;
   - whether yield was measured;
   - the number of replicates;
   - the units.
2. **Find the cell.** It is at `table` / `row_header` / `col_header`. Check that
   `cell_verbatim` matches the PDF/HTML **exactly**. If it doesn't, write
   `is_retention_relevant=extract_error` and stop.
3. **Decide relevance.** Write `yes` only if the cell (or the cell plus its raw counterpart in
   the same table) gives the effect of a named culinary process on a named target in a named
   food. Otherwise write `no`: control rows, statistics columns, p-values, sensory scores
   without a process contrast.
4. **Fill the mapping columns.** Use only what the paper states:

| Column | Allowed values | Rule |
|---|---|---|
| `ingredient_id` | `ING-<slug>`, e.g. `ING-broccoli` | the food as studied. Category-level foods get a category ING |
| `process_ids` | `PROC-` ids from `ledgers/process/proc_v0.csv`, `;`-separated, in order | unmapped verb → `PROC-UNMAPPED:<verb>`. Never pick the "closest" process |
| `conditions` | `T=100C(MEASURED); t=10min(MEASURED); medium=water(QUALITATIVE); water_handling=discarded(QUALITATIVE)` | anything not stated → leave out (it stays UNKNOWN) |
| `target` | the analyte as named in the paper, plus the PubChem CID if one compound | groups (e.g. "total phenolics") get no CID |
| `value_kind` | `RETENTION_PERCENT`, `RETENTION_FRACTION`, `CONCENTRATION`, `DELTA`, `DIRECTION_ONLY` | concentrations need the raw-food row of the **same** table to become retention, and that is a derivation the promotion script performs, not you |
| `basis` | `WET`, `DRY`, `UNSPECIFIED` | from Methods |
| `retention_method` | `TRUE_RETENTION` (yield-corrected), `APPARENT_RETENTION` (concentration ratio), `UNSPECIFIED`, `NOT_APPLICABLE` | true retention needs a measured cooking yield |
| `verifier`, `verified_utc` | your name; ISO time | — |

5. **Flags.** If the paper reports `< LOD` / `nd`, record that in `cell_flags` (it is a LEFT
   censor). `±` gives `parsed_sd`; check whether the paper uses SD or SE and add `SE` to
   `cell_flags` if it is SE.

## Tier

| Paper type | Tier |
|---|---|
| Primary study with measured conditions + replicates | **E2** |
| Primary study with qualitative conditions only | **E4** |
| Review or aggregated table | `origin_type=REVIEW_AGGREGATE`, at most **E4**. Check the cited primary study if you can |

## Never

- Never type a number that is not in the cell.
- Never convert units in your head. The promotion script does conversions and logs them.
- Never mark a row verified from the abstract or a figure alone (figures → `no`, note `figure_only`).
- Never verify your own extraction script's guess. The script makes no guesses, which is the point.
