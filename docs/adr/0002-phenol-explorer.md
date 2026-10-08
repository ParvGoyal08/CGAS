# ADR 0002 — Phenol-Explorer 3.0 acquisition (WP K4)

**Status:** PROPOSED — needs an H2 decision (new scraping target) · **Date:** 2026-10-08

## Context
- DEL-1's proposal names "public retention databases (Phenol-Explorer, USDA)".
- Phenol-Explorer 3.0 has **1,253 polyphenol retention factors** (Rothwell et al. 2013,
  *Database* bat070; CC-BY article).
- These factors would give DEL-2 a second, **multi-study** source. With it, a
  source-held-out split becomes possible; USDA R6 alone makes study-disjoint
  evaluation infeasible (DEL-2 card §F).

## Findings (2026-10-08)
| Check | Result |
|---|---|
| HTTPS | certificate mismatch (`*.wishartlab.com`, `lmdb.ca`) → TLS verification fails |
| HTTP | `/` 200, `/downloads` 200, `/robots.txt` 200 |
| robots.txt | every rule commented out → nothing disallowed |
| Bulk downloads | composition data, compounds, foods, structures, publications (CSV/XLS) — **no retention-factor file** |
| Retention factors | HTML only: `/retention-factors/polyphenols` (132 polyphenols with RF data; ~25 list pages, plus detail pages per polyphenol × process) |
| Terms of use | no `/terms` or `/about` text found; database reuse terms **unverified [U]** |

## Options
1. **Polite crawl** of the retention-factor pages.
   - Rate: 1 request / 2 s; contact UA; local cache; ~20 min.
   - Store **derived rows + citation + page URL**; no page text redistributed.
   - Every row tier E3, `source_family_id=PHENOL-EXPLORER-3.0`, `study_ids` from the
     publication links on each page.
   - Risk: unverified terms; data fetched over plain HTTP (integrity → `SNAP-` hashes of every page).
2. **Email the maintainers** (Wishart lab / INRAE) for an export — H1. Slow, but clean.
3. **Proceed without Phenol-Explorer.** DEL-1's ≥1,000-row minimum is already met by
   R6 (7,018 rows). DEL-2 keeps its pre-registered "study-disjoint infeasible" outcome.

## Recommendation
**Option 1 now, plus option 2 in parallel:** crawl politely, keep it internal, and ask
the maintainers to confirm reuse terms before any release. If the humans decline
H2, option 3 is fully consistent with both the course contract and the frozen DEL-2 card.

## Addendum 2026-10-08 — access-route audit

**Status: BLOCKED_EXTERNAL. This is not a project blocker.** The DEL-1 minimum of
≥1,000 rows is already met by USDA R6 (7,018 rows). DEL-2 keeps its pre-registered
outcome, "study-disjoint infeasible". What is blocked is only the *optional* second
source, and it is blocked on a reply from outside the team.

**Method.** Desk audit only. 10 pages fetched over plain HTTP (HTTPS still fails, see
Findings): 9 on phenol-explorer.eu and 1 on the Wishart-lab feedback host. Requests
went out one at a time, ≥12 s apart, 18:05–18:09 UTC. Raw HTML stayed in a session
scratchpad, outside the project. Nothing was crawled, bulk-downloaded or sent. Journal
metadata came from web search, PMC/OUP pages, Europe PMC REST, Crossref and Unpaywall.

### Pages checked on the site
| # | URL (http://phenol-explorer.eu…) | What it says |
|---|---|---|
| 1 | `/` | "Version 3.6". "Retention factors are available for 155 foods, 139 polyphenols, and 35 processes. They are derived from 129 publications." Lists developers (INRA, AFSSA, U. Alberta, U. Barcelona, IARC, In Siliflo). No licence or terms text. |
| 2 | `/downloads` | **Terms (verbatim):** "Phenol-Explorer is offered to the public as a freely available resource. Use and re-distribution of the data, in whole or in part, for commercial purposes requires explicit permission of the authors and explicit acknowledgment of the source material (Phenol-Explorer) and the original publications". Also: "We ask that users who download significant portions of the database cite the Phenol-Explorer paper". Current files (2016-12-10): composition data, compounds, metabolites, classifications, foods, publications, SMILES (XLS/CSV). The Access DB is described as "without the metabolism and retention factor components". **No retention-factor file.** |
| 3 | `/contact` | No e-mail address. "Please use the Feedback Form which will direct your message to the Phenol-Explorer curator through the Wishart Research Group web interface" → `http://feedback.wishartlab.com?site=phenol_explorer` |
| 4 | `/cite_us` | Repeats the terms on `/downloads`, word for word, and lists the papers to cite: Neveu 2010 bap024, Rothwell 2012 bas031, Rothwell 2013 bat070 (plus Rothwell 2015 MNFR). Adds: "The content of Phenol-Explorer is intended for educational and scientific research purposes only." |
| 5 | `/faqs` | "Can I export the data? Search results are easily exported as Excel file using the Export function." No licence or API mentioned. |
| 6 | `/credits` | Release 3.0 (retention factors) "was developed at INRA, Unité de Nutrition Humaine and IARC, Biomarkers Group", released June 2013. "Augustin Scalbert (INRA) coordinated the project." |
| 7 | `/retention-factors/polyphenols` | "The 132 polyphenols with retention factor data…"; "Displaying compound processings 1 - 25 of 602 in total" (25 pages). **No Export control** in the page markup. |
| 8 | `/food-processing/foods` | "The 155 foods with retention factor data…"; "1 - 25 of 316 in total" (13 pages). Defines RF = (conc. processed / conc. raw) × yield factor. No Export control. |
| 9 | `/food-processing/213/compounds` | A sample detail table (mean RF, min, max, SD, n, # refs), linking to `/retention-factors/details/<id>`. No Export control. |
| 10 | `http://feedback.wishartlab.com/?site=phenol_explorer` | Generic Wishart Research Group form. "Phenol-Explorer" is one of the "Regarding:" options. "By sending us your feedback with your name and email, you consent to allow us to store this information". |

Counts disagree between pages: the home page says 139 polyphenols, `/retention-factors/polyphenols` says 132, and bat070 says 161 "polyphenols or groups". The likely reason is aggregated groups versus individual compounds. **[U]**

### Licence and terms status
- **Database terms: FOUND** (pages 2 and 4 above). They are short, informal terms, **not a standard licence**:
  - **Commercial** use or redistribution needs explicit permission.
  - Acknowledging Phenol-Explorer and the original publications is required.
  - Citing the papers is requested.
  - The content is for "educational and scientific research purposes only".
  - The terms say nothing about **non-commercial** reuse or redistribution of derived rows, and nothing about automated access. robots.txt disallows nothing (Findings, above).
- **The article licences apply to the article text, not to the database.** The CC BY on bat070 does **not** relicense the RF data. The 1,253 RFs are data on the website, not content of the article.

### Supplementary-file / journal route: NOT AVAILABLE
| Paper | Licence (source) | Supplementary files | Contains RF table? |
|---|---|---|---|
| Rothwell 2013, *Database* bat070, PMC3792339 | CC BY 3.0. OUP/PMC: "This is an Open Access article distributed under the terms of the Creative Commons Attribution License" | **None.** No supplementary section on PMC or OUP; Europe PMC `hasSuppl=N` | No. The article describes "four tables that were added to the relational design" and access "through the existing … web interface" |
| Rothwell 2012, *Database* bas031, PMC3414821 | CC BY-NC (Europe PMC `license` field) | None (`hasSuppl=N`) | No (metabolism release) |
| Neveu 2010, *Database* bap024, PMC2860900 | CC BY-NC 2.5 (PMC: "permits unrestricted non-commercial use…") | Points to `…/bap024/DC1`, said to be "available at the Phenol-Explorer site" | No (predates RFs) |
| Rothwell 2015, *Mol Nutr Food Res* 59:160–170, doi 10.1002/mnfr.201400494 | Hybrid OA, **CC BY-NC-ND 4.0** (Crossref `license`, VoR; Unpaywall `oa_status=hybrid`) | **[U]**. Wiley returned 403 (Cloudflare) to automated fetches; not in Europe PMC | The abstract reports summary medians only, e.g. cooking "median RF = 0.45–0.70". Even if a supporting-information file exists, ND limits redistributing adaptations |

**Other repositories: none found.** Searches covered Zenodo, Figshare, GitHub, Kaggle, Hugging Face and data.inrae.fr. HAL-INRAE (hal-02651433) blocked the automated fetch (Anubis). The FAO INFOODS entry lists only "Free access", "Searchable web tool", with no licence. No legitimate redistribution of the RF table was found.

### Maintainers / contact
- **Official route (site):** the feedback form at `http://feedback.wishartlab.com/?site=phenol_explorer` ("Regarding: Phenol-Explorer"). Messages go "to the Phenol-Explorer curator through the Wishart Research Group web interface" (`/contact`). The site publishes no e-mail address.
- **Published e-mail (paper):** Augustin Scalbert, corresponding author of bat070, IARC Nutrition and Metabolism Section, Lyon. The paper gives "Email: scalberta@iarc.fr" (PMC3792339). The 2010 paper gives scalbert@clermont.inra.fr, which is probably stale since INRA became INRAE in 2020. Whether either address still works is **[U]**.
- **Hosting:** the Wishart Research Group, University of Alberta, hosts the site and runs the feedback system. The HTTPS certificate is for `*.wishartlab.com`.

### Recommendation
**(b) Request from maintainers. Option (a) does not exist.**
- **(a)** No official RF export or supplement exists (tables above).
- **(b) Primary route.**
  - Owner: Parv.
  - Draft: `docs/email_drafts/PE_maintainers_request.md`.
  - Gate: **H1** (both Kush and Parv approve).
  - Channel: submit through the official feedback form, with the same text e-mailed to scalberta@iarc.fr.
  - Done-check: a reply naming a permitted route, or 10 working days with no reply.
- **(c) Polite crawl.** The published terms do not forbid it for non-commercial, attributed research use, and robots.txt allows all. It still needs **a separate H2 approval**, which is not granted (STATUS.md row 6). If approved, the earlier Option 1 parameters stand, with these changes:
  - ≥10 s between requests (not 2 s), to match the DEC-025 practice.
  - ~38 list pages plus detail pages.
  - Derived rows + citation + URL only. No page text redistributed.
- **(d) Skip.** This is the default if (b) gets no answer and H2 declines (c). It is fully consistent with the course contract and the frozen DEL-2 card.

This addendum **supersedes the "Option 1 now" recommendation above**. Do not crawl until H2 is recorded in `DECISIONS.md`.
