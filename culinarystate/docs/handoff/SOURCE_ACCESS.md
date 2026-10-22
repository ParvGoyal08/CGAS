# SOURCE_ACCESS — every source in use, how it was obtained, and where its hash lives

| Source | ID | Obtained | Licence / terms | Snapshot ledger | Stored in git? |
|---|---|---|---|---|---|
| USDA Nutrient Retention Factors R6 | SRC-0001 | figshare download | CC0 | `ledgers/snapshots/snapshots.csv` (SNAP-0001…0003) | no (`data/raw` is ignored) |
| FSSAI Labelling & Display Regs (compendium v8) | — | fssai.gov.in PDF | public regulation | `authority_snapshots.jsonl` (SNAP-0004) | no |
| 35 + 24 open-access papers (Europe PMC JATS) | PMCIDs | Europe PMC REST | CC BY (only CC BY / BY-SA / CC0 stored) | `literature_snapshots.jsonl` | no (raw); extracted cells yes |
| PubChem structures | CIDs | PUG-REST | public domain data | `pubchem_snapshots.jsonl` | no |
| Kinouchi 2008 (arXiv v1) | SRC-L13E-KINOUCHI2008 | arxiv.org /pdf | arXiv non-exclusive | `l13e_snapshots.jsonl` | **never** (local only) |
| FoodOn | SRC-FOODON | GitHub release | see snapshot record | `foodon_snapshots.jsonl` | no |
| USDA FoodData Central (Foundation 2026-04-30; SR Legacy 2018-04) | SRC-USDA-FDC | fdc.nal.usda.gov | public domain (quote to be recorded) | `fdc_snapshots.jsonl` | no |
| A1 corpus (BBC Good Food names) | — | our A1 deliverable | local use only; aggregates only | — | no raw text |

**Re-fetch rule:** every raw file can be re-obtained from the URL in its snapshot record. The sha256 there must match, otherwise `gate.py` G-SNAP fails.
