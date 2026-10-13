# API_BLOCKERS — every external API/data route

| Route | Key needed? | Status | Terms recorded | Notes |
|---|---|---|---|---|
| RecipeDB API / bulk | yes (CoSyLab) | requested 2026-10-13 | pending | the brief's critical path |
| FlavorDB / FlavorDB2 | via CoSyLab | requested (mappings); names/IDs may need a follow-up | pending | D1 normalisation |
| Foodoscope API suite | yes | optional item in the email | pending | not required for the minimal brief |
| DietRx / SpiceRx / SustainableFoodDB | yes | not requested in email v2 | — | context only; not needed |
| Phenol-Explorer | no API; no export | maintainer request drafted | site terms quoted in ADR 0002 | crawl only with H2 |
| Europe PMC REST | no | in use (Crawl-Delay 10 s) | robots.txt honoured | open-access papers (DEC-019) |
| PubChem PUG-REST | no | in use (≤ 5 requests/s) | — | structures (DEC-019) |
| USDA R6 (figshare) | no | done (SNAP-0001…0003) | CC0 | — |
| USDA FoodData Central bulk | no (API key optional) | downloaded (SNAP-FDC-0001/0002) | **licence quote still to record** before use | DEC-041 H2-B |
| FoodOn (GitHub / OBO PURL) | no | downloaded (SNAP-FOODON-0001) | licence quoted in the snapshot | DEC-041 H2-A |
| arXiv | no | Kinouchi preprint (SNAP-L13E-0002) | non-exclusive licence; local only | — |
| Anthropic API | yes | not configured; `ClaudeBackend` refuses without H3 | — | optional |
| Ollama (local) | no | running (`qwen2.5:3b`) | — | dev + course ladder |
