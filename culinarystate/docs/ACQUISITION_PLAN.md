# Source, API and licence acquisition plan

Startup-contract item 9 (master prompt Part AF). Candidate sources are seeded in
`registry/datasets.csv` (13 rows). **No source has been contacted, downloaded or
scraped.** Every licence is marked `[U]` because none has been checked yet; the
checks are research nodes N1, N3, N14 and N17.

## Policy (Part R4, law B19)

- Official APIs, bulk dumps and licensed datasets come before scraping. **This
  plan proposes no new scraping.**
- Every source is recorded in `datasets.csv` before the first request, and needs
  **H2** approval.
- Each download writes a `SNAP-` record: retrieval timestamp, URL/DOI, content
  hash, licence snapshot, raw-storage permission, local path.
- Raw text is stored only where the licence permits. Otherwise only offsets,
  hashes and derived rows are kept.

## Order of operations

| Step | What | Depends on | Gate |
|---|---|---|---|
| 1 | Brief N1 — legality, copyright of recipe text, storage rules | — | — |
| 2 | Brief N3 — USDA R6, Phenol-Explorer 3.0, EuroFIR: formats, coverage, licence | — | — |
| 3 | Acquire the DEL-1 public sources (SRC-0001, SRC-0002) | N1, N3 | **H2** each |
| 4 | Send the Bagler email (`email_drafts/A2.1_bagler_api_request.md`) | humans edit it | **H1** |
| 5 | Run the §42 API audit when keys arrive; fill the `API-` ledger | step 4 | H2 per endpoint |
| 6 | Decide on the A1 corpus as DEL-3 input (SRC-0008) | N1 | **H2** — Q5 |
| 7 | Safety authorities for DEL-5 (SRC-0010, SRC-0011) | N14 | H2 |
| 8 | Portion and density sources for DEL-3 quantities (SRC-0009) | N17 | H2 |

## Proposed storage classes (to be confirmed by N1)

| Class | Meaning | Candidates |
|---|---|---|
| Store raw | Licence permits keeping the original | US-government data, if public domain is confirmed (SRC-0001, 0009, 0010) |
| Store derived | Keep extracted rows, hashes and offsets; not the original text | Phenol-Explorer until its terms are read; literature rows; the A1 corpus outside local development |
| Reference only | Cite and link; keep nothing | anything whose terms forbid storage |

## Fallbacks — already in the proposal (§8, "Risks")

- **API access delayed** → public downloads and web tables. DEL-1 depends only on
  public retention databases, so it is **not blocked** by the email.
- **Name normalisation without RecipeDB access** → normalise to FlavorDB's public
  names first, and add RecipeDB IDs when access arrives. This is a proposed
  workaround, not yet checked against FlavorDB's terms (N16).
- **DEL-3 input** → the A1 corpus (Q5), RecipeDB if granted, or an
  openly-licensed corpus (node N21, conditional).

## The A1 corpus — what it is, and why it needs a decision

| Fact (checked locally) | Value |
|---|---|
| Source | BBC Good Food, scraped 2026-09-08 for Assignment 1 |
| Recipes | 11,983 raw; 11,934 after cleaning |
| Step-level instruction text | present for 11,981 recipes |
| Existing per-step parse | `instruction_events.jsonl`: ingredients and utensils per step; **actions, duration, temperature and output state are all null** |
| Compliance record | A1 `DECISION_LOG.md`: robots.txt allowed the recipe paths |

It is the closest thing to "structured recipe tables / upstream parser output"
that DEL-3 says it consumes. But robots.txt permission to crawl is not
permission to reuse the text in a project, and the project plans to release a
benchmark. Hence the H2 question.
