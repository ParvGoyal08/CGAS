# RS-08 — Recipe NER / recipe semantic-parsing landscape: verified resource cards

| Priority | Block | Node | Date | Session |
|---|---|---|---|---|
| P0 | B08 (NER reproduction programme) | N27 | 2026-10-08 | Parv + Claude (desk research; web pages and papers only, no dataset/model downloads) |

**Status:** BRIEFED and awaiting review. The machine-readable registry is `registry/ner_resources.csv` (NERRES-01…18).

**Tags:** [V] = verified on the primary page or paper today. [C] = credible secondary source (a third-party listing or the citing paper). [U] = UNVERIFIED, with the reason given. No field was filled from memory. Where I could not open a source, the field says UNVERIFIED.

**`licence_verified` in the CSV:** `yes` means the licence field reflects what the primary source says, including a confirmed "none stated". `no` means the licence is unread, conflicting, or only partly read.

---

## Answer in 8 lines

1. **18 resources carded.** 13 are verified on primary sources. 4 are partially verified: Goel 2024 (data link not resolved), TASTEset 2.0 (paper text and DOI not read), GLiNER2 (benchmarks and model licences not read) and kNN-NER (method only). 1 is not found: published DeBERTa-v3+CRF recipe NER. A retrieval/kNN NER applied to recipes was also not found; it is recorded on the kNN-NER card.
2. **Name checks.** "JFC-Recipe" exists, but it is a *Japanese nutrient-estimation* dataset (food-item linking plus quantities), not English NER. "ARA" exists as *Aligned Recipe Actions* (EMNLP 2021), a cross-recipe action-alignment corpus. "ReciFineGold" and "RecipeRoBERTa-KA" exist. "RecipeBERT" is not a standalone recipe-NER model: it is a baseline label in Ibrahim et al. 2026, and the name is also used by an unrelated recommender. "RecipeDB 3.0" has no versioned release or paper. The only public artefact is the GitHub repo `cosylabiiit/RecipeDB3_NER_Research_Paper`, created 2026-07-06, with no licence.
3. **The plan's RecipeDB3 numbers are correct but mislabelled** [V, notebook outputs]. Ingredient macro-F1 is **0.9557**. However, the model is **`microsoft/deberta-base` (DeBERTa v1), not v3, with no CRF**. The test set is also used for epoch/model selection, and `B-SIZE` is mapped to `O`, so SIZE is not scored. Instruction NER gives **micro-F1 0.9258 / macro-F1 0.8698** (seqeval, spaCy blank `en`).
4. **Only one public corpus covers the whole cascade.** The English Recipe Flow Graph corpus (ERFG / r-FG; 300 recipes) has spans for food (including intermediates), tools, actions and states, plus a labelled flow graph with identity edges (F-eq, T-eq, A-eq). It is **available by email only, with no stated licence**. RISeC (MIT) is the open complement: PropBank-style relations plus zero anaphora.
5. **Best published span numbers:** RecipeRoBERTa-KA 90.37 F1 on ERFG and 98.01 / 96.21 on AR / GK (Ibrahim et al. 2026, Table 1). TASTEset v1 is 0.935 (BERT-large, 5-fold), and TASTEset 2.0 is 0.943 (GitHub README). **These numbers are not directly comparable.** Splits, scorers and label mappings all differ (see §Scorer).
6. **Licence blockers:** see the §Licence summary table. In short, the CoSyLab repos have no licence, ERFG is email-only, everything ReciFine/KA is CC BY-NC, RecipeDB is CC BY-NC-SA 3.0, and JFC-Recipe has a conflicting licence. Open and permissive: TASTEset v1 and 2.0 (MIT), RISeC (MIT), ARA (CC BY 4.0 data), ingredient-parser (MIT), NYT tagger (Apache-2.0) and GLiNER v2.1 (Apache-2.0).
7. **Recommended first CPU reproductions:** (1) RecipeDB3 instruction NER with spaCy; (2) Diwan/Goel Stanford-NER CRF on AR/GK; (3) the ingredient-parser CRF. Justification is in §Recommended. Items 1 and 2 are gated on Bagler's permission (H1/H2) because the repos have no licence.
8. **Decision enabled:** B08 can start with (3) now. (1) and (2) start once the A2.3 email (item 6, "permission to reuse the RecipeDB3 NER annotation data and notebooks") is answered. The shared scorer (§Scorer) must exist before any number is compared.

---

## Summary table

Key to the cascade columns: S = span, L = linking, A = attributes, E = events, C = coreference/identity/implicit arguments, I = intermediate entities, G = state/flow graph. ● = annotated with gold. ◐ = partial or weak. — = not covered.

| ID | Resource | Kind | Exists | Licence (short) | Availability | Size (headline) | S | L | A | E | C | I | G | CPU | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | RecipeDB NER v1 (Diwan et al. 2020; AR/GK) | dataset | yes | none stated (repo); RecipeDB site CC BY-NC-SA 3.0 | open repo, unlicensed | 6,612 train + 2,188 test ingredient phrases | ● | — | ● | ◐ | — | — | — | yes | V |
| 02 | RecipeDB ingredient NER (Goel et al. 2024) | dataset | yes | UNVERIFIED (data link not resolved) | "on GitHub" (link UNVERIFIED) | 6,611 / 26,445 / 88,526 phrases | ● | — | ● | — | — | — | — | yes (CRF/spaCy-CPU) | partial (data link U) |
| 03 | RecipeDB3 NER (CoSyLab GitHub) | dataset + notebooks | yes (no paper) | none stated (GitHub license=null) | open repo, unlicensed | 26,444 ingr. rows; instr. CSV 1.29 MB | ● | — | ● | ◐ | — | — | — | yes (instr.) / unknown (DeBERTa) | V |
| 04 | TASTEset v1 | dataset | yes | MIT | open | 700 recipes, 13,362 entities | ● | — | ● | — | — | — | — | unknown | V |
| 05 | TASTEset 2.0 | dataset | yes | MIT (GitHub); DataPort copy is subscription | open (GitHub) | 1,000 recipes, ~19,500 entities | ● | ◐ | ● | — | — | — | — | unknown | partial |
| 06 | ReciFineGold | dataset | yes | CC BY-NC 4.0 | open (HF) | 500 recipes | ● | — | ● | ◐ | — | ◐ | — | yes (eval) | V |
| 07 | ReciFine (silver) | dataset | yes | CC BY-NC 4.0 | open (HF) | 2.23M recipes, >97M entities | ◐ | — | ◐ | ◐ | — | ◐ | — | yes (as data) | V |
| 08 | RecipeBERT-KA / RecipeRoBERTa-KA | model | yes | CC BY-NC 4.0 | open (HF, 12 ckpts) | ~0.1B params each | ● | — | ● | ◐ | — | — | — | yes (inference) / unknown (train) | V |
| 09 | JFC-Recipe | dataset | yes (renamed scope) | CONFLICT: paper CC BY-NC 4.0 vs repo CC BY-SA 4.0 | annotations open; texts via Cookpad/NII-IDR | 1,985 recipes, 15,188 ingredients | — | ● | ● | — | — | — | — | partial | V (licence conflict) |
| 10 | English Recipe Flow Graph (ERFG / r-FG) | corpus | yes | none stated | email request | 300 recipes, 15,435 r-NEs, 15,861 edges | ● | — | ● | ● | ● | ● | ● | unknown | V |
| 11 | RISeC | corpus | yes | MIT | open | 260 recipes | ● | — | ● | ● | ● | ● | ◐ | unknown | V |
| 12 | ARA (Aligned Recipe Actions) | corpus | yes (renamed) | CC BY 4.0 (data), Apache-2.0 (code) | open | 110 recipes, 1,592 action pairs | ◐ | — | — | ● | ◐ | — | ◐ | unknown | V |
| 13 | ingredient-parser (strangetom) | tool | yes | MIT | open (PyPI 2.8.0) | 81,346 labelled sentences | ● | ◐ | ● | — | — | — | — | yes | V |
| 14 | NYT ingredient-phrase-tagger | tool | yes (archived 2019) | Apache-2.0 | open (archived) | ~180k examples | ● | — | ● | — | — | — | — | yes | V |
| 15 | DeBERTa-v3 + CRF for recipe NER | model | **NOT FOUND** | n/a | n/a | n/a | — | — | — | — | — | — | — | unknown | not found |
| 16 | GLiNER (v2.1 family) | model | yes | Apache-2.0 (v2/v2.1); CC BY-NC (v0/v1) | open | 166M–459M | ◐ | — | ◐ | — | — | — | — | yes | V |
| 17 | GLiNER2 / GLiNER2.5 | model | yes | Apache-2.0 (code); model cards UNVERIFIED | open | 74M–340M | ◐ | — | ◐ | — | — | — | — | yes (claimed) | partial |
| 18 | kNN-NER (retrieval-augmented NER) | model (method) | yes; **recipe use NOT FOUND** | UNVERIFIED | code on GitHub | n/a | ◐ | — | — | — | — | — | — | unknown | partial |

---

## Resource cards

### NERRES-01 — Legacy RecipeDB NER (Diwan, Batra, Bagler 2020): the AllRecipes (AR) / GeniusKitchen (GK) ingredient-phrase sets

- **Primary paper** [V]: N. Diwan, D. Batra, G. Bagler. *A Named Entity Based Approach to Model Recipes.* 36th IEEE ICDE 2020, DECOR Workshop (ICDEW 2020, pp. 88–93 per Ibrahim et al. 2026's reference list [C]). arXiv:2004.12184 (v1 only, 25 Apr 2020), https://arxiv.org/abs/2004.12184
- **Data URL** [V]: https://github.com/cosylabiiit/recipe-knowledge-mining (paper footnote 1: "All data and code used in this paper are available online on GitHub"). The repo lists `ar_train.tsv`, `ar_test.tsv`, `gk_train.tsv`, `gk_test.tsv`, `ar_gk_train.tsv`, `ar_gk_test.tsv`, `ar_complete_dataset.tsv`, `gk_complete_dataset.tsv`, `gk_ingredient_phrases.csv`, the folder `Relation Extraction In Instructions Section`, and `twitie_tag.jar`. The README says: "We are in the process of uploading the code and data presently and will finish soon."
- **Licence** [V]: **none stated** (no LICENSE file or label). Separately, the RecipeDB website says: "This work is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License" (cosylab.iiitd.edu.in/recipedb/). Whether the site licence covers the GitHub annotations is UNVERIFIED.
- **Size** [V]: Table III gives training/testing sizes of AllRecipes 1,470 / 483, FOOD.com 5,142 / 1,705, and BOTH 6,612 / 2,188 ingredient phrases. The conclusion says "a labelled dataset of 8800 Ingredient phrases". The phrases were sampled by POS-vector K-means (23 clusters) from 118,000 RecipeDB recipes. Instruction NER used "the recipes with the longest instructions section from 40 different cuisines … to further annotate 268 processes/techniques, ingredients, and 69 utensils"; the count of instruction recipes is not stated.
- **Label set** [V]: Ingredients (Table II) are NAME, STATE, UNIT, QUANTITY, SIZE, TEMP and DRY/FRESH. Instructions are PROCESS, UTENSIL and INGREDIENT (Fig. 4).
- **Splits** [V]: the fixed train/test sizes are in Table III. The paper also says "The models were validated by 5-fold cross validation." Whether the repo TSVs equal the Table III splits is UNVERIFIED (would need the data).
- **Availability:** open GitHub, but unlicensed. Reuse needs permission.
- **Reported metrics** [V]: Stanford NER (CRF), F1. The paper does not say whether it is micro or macro.
  - Table IV (rows = test set, columns = training set): AR test: AR **0.9682**, FOOD.com 0.9317, BOTH **0.9709**. FOOD.com test: 0.8672, **0.9519**, 0.9498. BOTH test: 0.8972, 0.9472, **0.9611**.
  - Table V (instructions): Processes P 0.92 / R 0.85 / **F1 0.88**. Utensils P 0.94 / R 0.86 / **F1 0.90**.
  - Relations: there is no gold evaluation. A rule-based dependency-parse tuple extraction was run on 40,000 recipes (174,932 steps): "an instruction yielded 6.164 relations with a standard deviation of 5.70".
- **Independent reproduction** [V]: Goel et al. 2024, Table 1, re-ran Stanford NER and got "the same results for seven out of nine experiments, and for the rest of the two, the deviation was <1%". Their reproduction scored AR→AR 96.82, GK→GK 95.16 and Both→Both 95.52.
- **Scope:** ingredient phrases with attributes (quantity, unit, state, size, temperature, dry/fresh). Instructions have processes and utensils. Events are only as unscored rule tuples. There are no edges, coreference or intermediates.
- **Protocol warning** [V]: inputs were preprocessed by "eliminating stop words, lemmatizing all words using WordNet Lemmatizer, and converting the text to lower case". Character offsets are therefore not raw-text offsets.
- **CPU:** **yes**. Goel et al. trained Stanford NER "using CRFClassifier with default parameters on an 8 GB CPU RAM system" [V]. The Stanford NER software licence is UNVERIFIED (not checked).
- **Cascade relevance:** this is the source of the project's "RecipeDB 7 tags" legacy adapter. It is a good **attribute-span** baseline for ingredient lines. Its instruction labels are coarse and there is no graph.

### NERRES-02 — RecipeDB ingredient NER datasets (Goel et al. 2024)

- **Primary paper** [V]: M. Goel, A. Agarwal, S. Agrawal, J. Kapuriya, A. V. Konam, R. Gupta, S. Rastogi, Niharika, G. Bagler. *Deep Learning Based Named Entity Recognition Models for Recipes.* LREC-COLING 2024, pp. 4542–4554. https://aclanthology.org/2024.lrec-main.406/ ; arXiv:2402.17447 (v2 6 Jun 2024). The paper itself is "© 2024 ELRA … CC BY-NC 4.0".
- **Data URL:** the paper says (§8) "All relevant code files and datasets are available on GitHub". **The hyperlink target is UNVERIFIED**: the PDF link annotation could not be extracted, and the arXiv page lists no code link. One candidate is `cosylabiiit/RecipeDB3_NER_Research_Paper` (NERRES-03), whose ingredient set has 26,444 rows against this paper's 26,445 augmented phrases. **The match is a hypothesis, not verified.**
- **Licence:** UNVERIFIED (data link not resolved).
- **Size** [V]: Manually_Annotated has 6,611 train + 2,187 test phrases. Diwan reports a 2,188 test set (an off-by-one discrepancy). Augmented has 26,445 phrases, built with label-wise token replacement, WordNet synonym replacement and shuffle-within-segments. Machine_Annotated is 88,526 phrases, a 25% stratified sample (2,067 clusters) of 349,762 unique RecipeDB phrases taken from 1,150,000. They were labelled by Stanford NER and then corrected by programmatic error-pattern fixes.
- **Label set** [V]: name, quantity, unit, df (dry/fresh), state, size and temp. These are 7 tags; the few-shot prompt lists `[QUANTITY, UNIT, NAME, TEMP, STATE, SIZE, DF, O]`.
- **Splits** [V]: every model is tested on the same 2,187-phrase manually annotated test set.
- **Metric** [V]: "We employ macro-F1 score, precision, and recall". The tag-wise F1 is averaged with equal weight per label.
- **Reported metrics** [V], Table 2 (F1 / P / R, %, on the 2,187-phrase test set; columns are the training sets):

| Model | Manually_Annotated | Augmented | Machine_Annotated |
|---|---|---|---|
| spaCy-transformer (en_core_web_trf) | **95.90** / 95.89 / 95.91 | **96.04** / 96.05 / 96.04 | **95.71** / 95.73 / 95.69 |
| spaCy-CPU optimized (en_core_web_lg) | 94.46 / 94.52 / 94.41 | 94.91 / 94.92 / 94.90 | 91.30 / 91.36 / 91.24 |
| Stanford NER | 95.52 / 95.64 / 95.39 | 95.16 / 94.37 / 95.96 | 89.9 / 91.31 / 88.53 |
| BERT (base) | 94.00 / 94.70 / 94.10 | 93.60 / 93.70 / 94.10 | 90.30 / 91.50 / 90.20 |
| flair (xlm-roberta-large) | 95.01 / 96.11 / 96.05 | 94.45 / 95.87 / 96.14 | 89.85 / 88.71 / 89.22 |

  - Table 3 shows few-shot LLMs (macro / micro F1): LLaMA2-7b 5.88 / 44.29, LLaMA2-13b 17.06 / 54.20, Mistral-7b 32.78 / 47.51, Vicuna-7b 32.90 / 51.41.
- **Hardware** [V]: the transformers ran on "an NVIDIA A100 80GB PCIe GPU … batch size of 44 and up to 12 epochs". Stanford NER ran on an 8 GB CPU-RAM machine.
- **Scope:** ingredient lines only. The paper says: "Our present study focuses on only ingredient phrases while not accounting for the recipe instructions".
- **CPU:** **yes** for the Stanford NER and spaCy-CPU (`en_core_web_lg`) rows. The transformer rows were GPU-run and their CPU feasibility is unknown.
- **Cascade relevance:** ingredient span and attribute layer. The 88,526 silver set is a candidate weak-supervision pool once the licence is resolved.

### NERRES-03 — "RecipeDB3" NER (CoSyLab GitHub; no paper found)

- **Existence check:** **no "RecipeDB 3.0" release, version label or paper was found.** I searched the web, read the RecipeDB website (no version label) and read the arXiv abstract of Bagler's *A generative grammar of cooking* (2211.09059), which mentions no RecipeDB3 or NER. The only public artefact is the repo below.
- **Data and code URL** [V]: https://github.com/cosylabiiit/RecipeDB3_NER_Research_Paper. It was created 2026-07-06 and last pushed 2026-07-07 (GitHub API). Tree:
  - `Annotation_Data/Ingredient_Annotated_Dataset.csv` (1,675,725 B)
  - `Annotation_Data/Instructions_Annotated_Dataset.csv` (1,289,020 B)
  - `NER_Models/Ingredients_NER_Model_DeBERTa.ipynb`
  - `NER_Models/Instruction_NER_Model_Spacy.ipynb`
  - `README.md` (174 B)
- **Licence** [V]: **none**. The GitHub API returns `"license": null`, and there is no LICENSE file.
- **Primary paper:** **NOT FOUND**. The repo name implies a paper, but none is linked or indexed.
- **Ingredient notebook** [V] (read from the notebook source and outputs):
  - Data: `'/kaggle/input/recipedb-bio/BIO_Annotated_RecipeDB_data.csv'`, "Shape: (26444, 2)". This is **not the same filename as the repo CSV**, so equivalence is UNVERIFIED.
  - Split: `train_test_split(data, test_size=0.20, random_state=48)`, giving **21,155 train / 5,289 test**. There is **no validation set**. "The test set is used for per-epoch evaluation and best-model selection" on `macro avg` F1.
  - Model: `MODEL_CHECKPOINT = 'microsoft/deberta-base'` (DeBERTa **v1**), `AutoModelForTokenClassification`, **no CRF**. MAX_LEN 128, batch 16, 15 epochs, lr 5e-5, AdamW. Subword continuations are set to -100, so scoring is on first sub-tokens. The device printed was `cuda`.
  - Labels: `O, B/I-NAME, B/I-QUANTITY, B/I-UNIT, B/I-STATE, B/I-TEMP, B/I-DF`. **`B-SIZE` appears in the data but is not in `label_dict` and is mapped to `O`**, so SIZE is dropped from training and scoring.
  - Scorer: `seqeval.metrics.classification_report(..., output_dict=True, digits=4)` in default mode (see §Scorer).
  - Final test report (epoch 15, also the best epoch): **micro F1 0.9603, macro F1 0.9557**, weighted 0.9604, support 18,553. Per label (F1, support): DF 0.9666 (490), NAME 0.9308 (6,015), QUANTITY 0.9879 (5,157), STATE 0.9493 (2,513), TEMP 0.9238 (113), UNIT 0.9757 (4,265).
- **Instruction notebook** [V]:
  - Data: `'/content/RecipeDB3_BIO.csv'`. This is also not the repo filename; equivalence is UNVERIFIED. Rows whose token and tag counts differ are dropped before the split.
  - Split: `train_test_split(TRAIN_DATA, test_size=0.2, random_state=42)`. Train/test counts are not printed.
  - Model: `spacy.blank("en")` with an `ner` pipe, 10 iterations, `minibatch(size=8)`, `drop=0.3`. No pretrained vectors and no transformer.
  - Labels (12): ACTION, INGREDIENT, QUANTITY, UNIT, STATE, FORM, DRYFRESH, SIZE, PREPROCESS, TIME, TEMPERATURE, UTENSIL.
  - Scorer: character spans are aligned to tokens, then scored with `seqeval` `classification_report`.
  - Results: **micro P 0.9227 / R 0.9289 / F1 0.9258** (support 6,345), **macro F1 0.8698**, weighted F1 0.9255. Per-label F1: ACTION 0.9039, DRYFRESH 0.8308, FORM 0.9787, INGREDIENT 0.9684, PREPROCESS 0.5000, QUANTITY 0.6381, SIZE 0.9239, STATE 0.9844, TEMPERATURE 0.8798, TIME 0.9469, UNIT 0.9441, UTENSIL 0.9383.
- **Checks against the project plan** (`Plan_SSOT15_v4_0.md` lines 392, 699, 702):
  - The numbers 0.9557 / 0.9258 / 0.8698 and the weak labels (QUANTITY 0.638, PREPROCESS 0.50, DRYFRESH 0.83, TEMPERATURE 0.88) are **verified**.
  - "DeBERTa" should read **DeBERTa-base v1, no CRF, test-set model selection, SIZE excluded**.
  - The "5.1% exact / 13.6% number-masked duplicates" claim is **UNVERIFIED**; it needs the data, which needs approval.
  - Hypothesis to test after approval: if the 26,444 rows are Goel's augmented set (26,445), a random split puts augmented variants of the same seed phrase on both sides.
- **Scope:** ingredient lines (6 scored attribute labels) and instruction spans (actions, utensils, ingredients, quantities, time, temperature, states). There are no edges, coreference or intermediates.
- **CPU:** instruction notebook **yes**, because it is a blank spaCy CNN pipeline. Ingredient DeBERTa-base, 15 epochs on 21k phrases: **unknown**. It was run on CUDA, so a timing probe is needed.
- **Cascade relevance:** the most direct **prior baseline for the project's span stage** on RecipeDB text. It is the B08 "reproduce then beat" target.

### NERRES-04 — TASTEset (v1)

- **Primary paper** [V]: A. Wróblewska, A. Kaliska, M. Pawłowski, D. Wiśniewski, W. Sosnowski, A. Ławrynowicz. *TASTEset – Recipe Dataset and Food Entities Recognition Benchmark.* arXiv:2204.07775 (v1 only, 16 Apr 2022; no journal-ref). https://arxiv.org/abs/2204.07775
- **Data URL** [V]: https://github.com/taisti/TASTEset (`data/TASTEset.csv`). The paper links the repo "for source code and models' details".
- **Licence** [V]: "MIT License", "Copyright (c) 2022 taisti". Recipe text was scraped from allrecipes.com, food.com, tasty.co and yummly.com; the upstream text rights are UNVERIFIED.
- **Size** [V]: "700 sets of ingredients from recipes were manually annotated"; "3,788 ingredients"; 13,362 entities.
- **Label set and counts** [V] (Table 1): FOOD 4,020; QUANTITY 3,780; UNIT 3,172; PROCESS 1,091; PHYSICAL QUALITY 793; COLOR 231; TASTE 126; PURPOSE 94; PART 55. BRAT span annotation; **discontinuous entities allowed**. BIO for the BERT models; span classification for LUKE.
- **Splits** [V]: 5-fold cross-validation, seed 42; grid search over epochs and learning rate. No fixed test split is published.
- **Metric** [V]: F1 "with exact-boundary and type matching (via the nervaluate module)", i.e. nervaluate *strict*. Whether "All" is micro or macro is **not stated**.
- **Reported metrics** [V], Table 2 (mean ± sd over 5 runs):

| Entity | BERT-base-cased | BERT-large-cased | FoodNER | BERT with CRF | LUKE |
|---|---|---|---|---|---|
| FOOD | 0.889±0.013 | 0.898±0.012 | 0.888±0.010 | 0.895±0.013 | **0.915±0.005** |
| QUANTITY | 0.983±0.004 | 0.982±0.007 | **0.985±0.004** | 0.980±0.006 | 0.975±0.010 |
| UNIT | **0.979±0.005** | 0.976±0.009 | **0.979±0.005** | 0.975±0.006 | 0.976±0.006 |
| PROCESS | **0.930±0.006** | 0.927±0.015 | 0.921±0.007 | 0.913±0.019 | 0.916±0.021 |
| PHYSICAL QUALITY | 0.797±0.011 | 0.795±0.025 | **0.804±0.015** | 0.772±0.003 | 0.767±0.035 |
| COLOR | 0.873±0.039 | 0.910±0.039 | **0.913±0.037** | 0.894±0.046 | 0.872±0.051 |
| TASTE | 0.772±0.115 | 0.781±0.089 | 0.769±0.116 | **0.789±0.093** | 0.655±0.120 |
| PURPOSE | 0.789±0.145 | **0.853±0.141** | 0.801±0.140 | 0.821±0.127 | 0.684±0.176 |
| PART | 0.705±0.115 | **0.801±0.034** | 0.744±0.127 | 0.730±0.091 | 0.786±0.10 |
| **All** | 0.932±0.008 | **0.935±0.011** | 0.932±0.006 | 0.929±0.008 | 0.927±0.008 |

  - **Discrepancy** [V]: the abstract says "The best model achieved, on average, 0.95 F1 … from 0.781 to 0.982", but Table 2's best "All" is 0.935. **Cite Table 2.** The paper is also inconsistent about whether "BERT with CRF" uses BERT-base-cased or BERT-large-cased.
  - Agreement: not reported.
- **Scope:** ingredient lines only. Food, quantity, unit, process (e.g. "chopped"), quality, colour, taste, purpose, part.
- **CPU:** **unknown**. The hardware is not stated in the extracted text. A BERT-base fine-tune on 700 ingredient lists is plausibly CPU-feasible, but that is unmeasured.
- **Cascade relevance:** ingredient span and attribute layer. It is the **cleanest-licensed strict-span benchmark**, which makes it the scorer-calibration anchor for nervaluate *strict*.

### NERRES-05 — TASTEset 2.0

- **Primary paper** [C]: A. Ławrynowicz, A. Wróblewska, A. Kaliska, M. Pawłowski, D. Wiśniewski, W. Sosnowski, J. Dutkiewicz. *Fine-Grained and Complex Food Entity Recognition Benchmark for Ingredient Substitution.* K-CAP '23 (12th Knowledge Capture Conference, Pensacola, 5–7 Dec 2023), pp. 25–29, ACM. The metadata comes from search snippets of the Poznań University of Technology record and DBLP. **The DOI and paper text are UNVERIFIED** (DBLP and the PUT page were bot-blocked).
- **Data URL** [V]: https://github.com/taisti/TASTEset-2.0 (`data/TASTEset.csv`, with columns `ingredients`, `ingredients_entities`). An IEEE DataPort copy also exists: "TASTEset - Recipe and Food Entities Dataset", DOI 10.21227/11bb-v380. **"This dataset requires an IEEE DataPort Subscription to access."**
- **Licence** [V]: GitHub label "MIT license" (LICENSE file; full text not read). The IEEE DataPort page states no licence.
- **Size** [V]: "1,000 manually annotated recipes' ingredients" (README). DataPort says "about 19,500 entities".
- **Label set** [V] (15): FOOD, UNIT, QUANTITY, PHYSICAL QUALITY, PROCESS, COLOR, TASTE, PURPOSE, PART, TRADE NAME, DIET, EXAMPLE, EXCLUDED, EXCLUSIVE, POSSIBLE SUBSTITUTE.
- **Splits** [V]: 5-fold CV (README).
- **Reported metrics** [V] (README; F1 on "all", mean ± sd over folds; results "do not include the rarest entities" EXCLUDED, EXCLUSIVE, POSSIBLE SUBSTITUTE): BERT-base-uncased 0.933±0.007; BERT-base-cased 0.941±0.006; **BERT-large-cased 0.943±0.004**; BioBERT 0.842±0.018; FoodNER 0.939±0.005; BERT with CRF 0.938±0.003; LUKE 0.928±0.005. Ibrahim et al. 2026 cite 94.30 as the TASTEset2 SOTA [V], which is consistent.
- **Scope:** ingredient lines, plus substitution-oriented labels (EXAMPLE / POSSIBLE SUBSTITUTE / EXCLUDED / EXCLUSIVE).
- **CPU:** unknown (same reasoning as v1).
- **Cascade relevance:** span and attribute layer. The substitution labels give weak **linking/alternatives** signals ("or", "e.g.", "such as"), which matter for one-to-many ingredient lines.

### NERRES-06 — ReciFineGold (gold, 500 recipes)

- **Primary paper** [V]: N. Ibrahim, R. Ravikumar, R. Stevens, R. Batista-Navarro. *ReciFine: Finely Annotated Recipe Dataset for Controllable Recipe Generation.* Findings of EACL 2026, pp. 4058–4074. DOI 10.18653/v1/2026.findings-eacl.210. https://aclanthology.org/2026.findings-eacl.210/
- **Name check:** the name "ReciFineGold" appears on GitHub and HF, not in the paper pages read (pp. 1–6). The README describes it as "a manually annotated gold-standard dataset of 500 real-world recipes with span-level semantic labels" [V].
- **Data URL** [V]: https://huggingface.co/datasets/nuhuibrahim/recifinegold (json; 500 rows; one `train` split; columns `id`, `text`, `label` = list of {start, end, tag}). Code: https://github.com/nuhu-ibrahim/ReciFine
- **Licence** [V]: HF "cc-by-nc-4.0". The repo LICENSE.md says: "This library is licensed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)". The paper says: "All code, datasets and pretrained model weights are released publicly under CC BY-NC 4.0". Upstream RecipeNLG text terms are UNVERIFIED.
- **Size and annotation** [V]: 500 recipes randomly sampled from RecipeNLG and annotated by two annotators "following the annotation guidelines defined in the ERFG corpus". **IAA F1 = 91.53%** (one annotator treated as gold).
- **Label set** [V] (10; ERFG scheme): FOOD, TOOL, DURATION, QUANTITY, ACTION_BY_CHEF, ACTION_BY_CHEF_DISCONTINUOUS, ACTION_BY_FOOD, ACTION_BY_TOOL, FOOD_STATE, TOOL_STATE. Character offsets.
- **Splits** [V]: the paper's protocol puts 300 recipes (60%) into training and 200 (40%) into test. **The HF release has a single 500-row split; the 300/200 ids are UNVERIFIED.**
- **Reported metrics** [V], Table 3 (P / R / F1):
  - Trained on ERFG only, scored on the 500 recipes: BERT-NER baseline 79.03 / 79.75 / 79.39; RecipeBERT-KA 82.71 / 81.86 / 82.28; **RecipeRoBERTa-KA 83.78 / 83.24 / 83.51**.
  - With +300 ReciFineGold training recipes (*), scored on the remaining 200: RecipeBERT-KA* 95.56 / 95.86 / **95.71**; RecipeRoBERTa-KA* 95.53 / 95.91 / **95.72**.
- **Scope:** instruction-level spans. Foods (ERFG F includes intermediate products), tools, durations, quantities, three action types, and food and tool states. **There are no edges.**
- **CPU:** **yes** for evaluation. It is 667 kB of data, and scoring is trivial.
- **Cascade relevance:** the most useful **open (NC) gold for instruction spans** in the ERFG scheme. It is an out-of-distribution test for anything trained on ERFG.

### NERRES-07 — ReciFine (silver, 2.2M recipes)

- **Paper:** as NERRES-06. **Data** [V]: https://huggingface.co/datasets/nuhuibrahim/recifine (csv; "2.23M rows"; one `train` split; 16 columns including title, ingredients, directions, link, source, NER, and one column per entity type). **Licence** [V]: "cc-by-nc-4.0".
- **Size** [V]: "over 97 million entities across ten entity types from 2.2 million recipes" (abstract).
- **How it was made** [V]: RecipeRoBERTa-KA was run per sentence and per entity type over RecipeNLG directions. **The labels are model output (silver).**
- **Metrics:** none of its own. Its quality proxy is Table 3 above.
- **Scope:** instruction-level spans for all 10 ERFG types. No edges.
- **CPU:** usable as data on CPU. At 2.23M rows, only subsets are practical.
- **Cascade relevance:** a weak-supervision and pre-training pool for the span stage. **Do not use it as an evaluation set.**

### NERRES-08 — RecipeBERT-KA / RecipeRoBERTa-KA (knowledge-augmented, entity-type-specific token classification)

- **Primary paper** [V]: N. Ibrahim, R. Stevens, R. Batista-Navarro. *Knowledge Augmentation Enhances Token Classification for Recipe Understanding.* EACL 2026 (Long), pp. 2776–2788. https://aclanthology.org/2026.eacl-long.127
- **Existence** [V]: both models exist.
  - **"RecipeBERT" (no -KA)** in this paper is the *baseline* multi-entity token classifier (Table 1, "Baseline (Ours)"). On HF it is `nuhuibrahim/recifinegold-recipebert-trad`.
  - An unrelated "RecipeBERT" exists: Divya Meredy, Univ. of Cincinnati, 2024, Zenodo record 14041762, CC BY 3.0 US. **It is a recommender ("ranks recipes based on semantic similarity"), not NER** [V].
- **Model URLs** [V]: HF collection https://huggingface.co/collections/nuhuibrahim/recifine has 12 checkpoints: `nuhuibrahim/recifinegold-{recipebert,reciperoberta}-{ka-question,ka-entity-type,ka-definition,ka-example,ka-all,trad}`, about 0.1B params each. The card for `…-reciperoberta-ka-question` says licence "cc-by-nc-4.0", base model RoBERTa-base, training data `nuhuibrahim/recifinegold`. **Checkpoints for the 7 benchmarks in Table 1 were not found**; only ReciFineGold-trained variants are listed [U].
- **Method** [V]:
  - Input is `[CLS] knowledge-context [SEP] sentence [SEP]`.
  - **One entity type per forward pass**, with a BIO label set per type (ETS).
  - Five context types: entity-type name, question, definition, example, or combined.
  - Training on 2× A100 80GB, AdamW lr 2e-5, up to 30 epochs (10 for FINER and the combined setups).
- **Datasets used** [V]: FINER (Komariah & Sin 2022), TASTEset 1 & 2, AR and GK (Diwan 2020), FoodBase (Popovski 2019) and ERFG. The authors re-split them; Table 10 gives positive/negative counts per type per split. Entity types were mapped (e.g. `name` in AR/GK, `ingredient` in FINER and `food` in TASTEset → INGREDIENT). The paper notes that ERFG `quantity` = number + unit, while other sets separate QUANTITY and UNIT.
- **Metric** [V]: "token-level precision, recall and F1 scores under strict span and type matching". The wording mixes token-level and span-level, so treat it as ambiguous.
- **Reported metrics** [V], Table 1 (F1). The best KA context is shown, and * marks significance over the prior SOTA:

| | FINER | TASTEset1 | TASTEset2 | AR | GK | FoodBase | ERFG |
|---|---|---|---|---|---|---|---|
| RecipeRoBERTa (baseline) | 93.10 | 93.78 | 92.96 | 96.22 | 94.00 | 97.15 | 86.51 |
| RecipeBERT (baseline) | 92.92 | 94.09 | 93.40 | 95.89 | 93.90 | 97.12 | 86.25 |
| SOTA (prior work) | 96.09 | 93.50 | 94.30 | 96.82 | 95.19 | 96.05 | 87.60 |
| RecipeRoBERTa-KA | 98.30 | 89.66 | 88.47 | **98.01*** | **96.21*** | 97.40 | **90.37*** |
| RecipeBERT-KA | **98.32*** | 89.85 | 87.84 | 97.80 | 95.97 | **97.85*** | 89.33 |

  - Table 3 (RecipeRoBERTa-KA, combined context, 10 seeds): FINER 98.20±0.03; TASTEset1 89.74±0.42 (−3.76, not significant); TASTEset2 87.99±0.44 (−6.31); AR 97.99±0.23; GK 96.28±0.04; FoodBase 97.37±0.23; ERFG 90.14±0.23.
  - **KA loses on TASTEset 1/2.** The authors say "baseline training performs better in structurally simple datasets like TASTEset 1 & 2".
  - **Caveat:** the "SOTA (prior work)" column comes from other papers' splits and scorers (e.g. AR 96.82 is Diwan's Stanford NER on Diwan's split). The deltas are therefore cross-protocol.
  - The ReciFine paper's Table 2 on the ERFG test set gives BERT-NER 86.50 / 88.80 / 87.60, RecipeBERT-KA 89.93 / 89.74 / 89.33 and **RecipeRoBERTa-KA 90.05 / 90.70 / 90.37**.
- **Scope:** span recognition across ingredient-line and instruction corpora. No edges.
- **CPU:** inference **yes**, since the models are base-size. **But ETS needs one pass per entity type (10 for ERFG).** CPU training cost is unknown.
- **Cascade relevance:** the current published SOTA for ERFG spans. The CC BY-NC licence limits reuse to non-commercial research.

### NERRES-09 — JFC-Recipe (the name is correct; scope is Japanese nutrient estimation, not NER)

- **Primary paper** [V]: K. Shirai, Y. Yamakata, H. Kameko, A. Sunto, J. Harashima, S. Mori. *JFC-Recipe: A Dataset for Nutrient Estimation from Japanese User-Generated Cooking Recipes.* LREC 2026, pp. 6349–6360. https://aclanthology.org/2026.lrec-1.504/
- **Data URL** [V]: https://github.com/ku-lsta/JFC-Recipe. It contains `annotation.csv` (recipeID, servings, food-item ID, food name, amount, unit) and `conversion.csv` (grams per food-item × unit; "-1" = not annotated). **The recipe texts are not included.** The README says they come from the Cookpad dataset via NII IDR. The IDR access terms are UNVERIFIED (page returned 404).
- **Licence: CONFLICT** [V]. The paper (§9) says "Our annotation dataset is available at our project page under CC BY-NC 4.0 license". The repo LICENSE file says "Attribution-ShareAlike 4.0 International" (CC BY-SA 4.0). **This must be resolved with the authors.**
- **Size** [V]: 1,985 recipes; 15,188 ingredients. Food items are linked to the Standards Tables of Food Composition in Japan (2,538 items), giving 668 labels including "water" and "N/A". There are 20 unit categories and a manually built weight table.
- **Agreement** [V] (Table 6, 100 recipes): food item κ 75.5%; amount 89.0% (match within 0.01); unit κ 88.2%.
- **Splits** [V]: 7:1:2 train/val/test, five different random splits, mean ± sd.
- **Reported metrics** [V]:
  - Quantity estimation accuracy: **88.9%** (full data).
  - Number-of-servings accuracy: **93.9%**.
  - Food-item estimation (ingredient-level accuracy and macro-F1) is reported **only in figures** (Fig. 3; it rises with data). There is no table, so exact numbers are UNVERIFIED.
  - Models: char-level Japanese BERT (classification) and Llama-3-Swallow-8B with LoRA (generation, trie-constrained decoding).
- **Scope:** ingredient lines (Japanese). **Linking** to a food-composition KB, plus quantity and unit to grams. There are no spans in instructions, events or graphs.
- **CPU:** partial. The BERT-classifier path is plausible on CPU (unmeasured). The 8B LoRA path needs a GPU.
- **Cascade relevance:** the best-documented precedent for the **linking → attributes (grams)** stages and their agreement metrics. It is not usable as English NER data.

### NERRES-10 — English Recipe Flow Graph corpus (ERFG / r-FG; Yamakata, Mori, Carroll 2020)

- **Primary paper** [V]: Y. Yamakata, S. Mori, J. Carroll. *English Recipe Flow Graph Corpus.* LREC 2020, pp. 5187–5194. https://aclanthology.org/2020.lrec-1.638 . The paper itself is "© ELRA, licensed under CC-BY-NC".
- **Data URL** [V]: https://sites.google.com/view/yy-lab/resource/english-recipe-flowgraph . Access is by email: "Please email me (yamakata [at] mi.u-tokyo.ac.jp)" with name, affiliation and purpose. Files are `*.list` (r-NE labels) and `*.flow` (edge lists), space-separated, with `#` comment lines.
- **Licence** [V]: **none stated** on the resource page.
- **Size** [V]: 300 recipes from Allrecipes UK/Ireland. 100-r was sampled per dish category; 200-r was sampled at random. 38,062 tokens; 15,435 r-NEs (Table 2/3); 15,861 gold edges (Table 6).
- **Label set** [V]:
  - r-NE tags (Table 1): F (food, "also intermediate products"), T (tool), D (duration), Q (quantity), Ac (action by chef), Ac2 (discontinuous Ac), Af (action by food), At (action by tool), Sf (food state), St (tool state). Tagging is IOB2.
  - Edge labels (Table 4): Agent, Targ, Dest, t-comp, F-comp, **F-eq, F-part-of, F-set, T-eq, T-part-of, A-eq**, V-tm, other-mod.
- **Agreement** [V]: r-NE P 89.9 / R 92.2 / **F1 90.5** (100-r). Flow graph P 84.4 / R 80.4 / **F1 82.3**.
- **Splits** [V]: NER uses 10-fold CV with 80% train, 10% tuning, 10% test. The flow graph uses 10-fold with 270 train / 30 test. **There is no fixed public split.**
- **Reported metrics** [V]:
  - BERT-NER overall P 86.5 / R 88.8 / **F1 87.6** (Table 2). By subset: 100-r 84.4, 200-r 86.7. Per tag (Table 3): F 92.1, T 88.9, D 88.8, Q 73.7, Ac 92.7, Ac2 45.3, Af 50.9, At 17.1, Sf 68.6, St 82.0.
  - Edge estimation (Table 5): gold r-NEs P 73.7 / R 68.6 / **F1 71.1**; automatic r-NEs **F1 43.3**.
  - The abstract says "71.1 to 87.5 F1" against the table's 87.6. **Cite the table.**
  - Later results on ERFG: Donatelli et al. 2021 [V] tagger 89.6±0.3 (ELMo BiLSTM-CRF) and parser 78.2±0.0 (gold tags) / 72.3±0.8 (end-to-end); Ibrahim et al. 2026 RecipeRoBERTa-KA 90.37 (own split).
- **Scope:** **full cascade.** Spans (food including intermediates, tools, actions, states, durations, quantities), events (actions and their arguments), identity edges (F-eq / T-eq / A-eq ≈ coreference), part-of and set edges, and a flow DAG.
- **CPU:** unknown. Small data (300 recipes) suggests CPU training of a small tagger is feasible, but that is unmeasured. The original edge model is a log-linear MST that is CPU-friendly by design; that is an inference.
- **Cascade relevance:** **highest of all resources.** It is the only public gold with spans, intermediates, identity edges and a graph. Its scheme is reused by ReciFine and ReciFineGold.

### NERRES-11 — RISeC (Recipe Instruction Semantics Corpus)

- **Primary paper** [V]: Y. Jiang, K. Zaporojets, J. Deleu, T. Demeester, C. Develder. *Recipe Instruction Semantics Corpus (RISeC): Resolving Semantic Structure and Zero Anaphora in Recipes.* AACL-IJCNLP 2020, pp. 821–826. https://aclanthology.org/2020.aacl-main.82
- **Data URL** [V]: https://github.com/YiweiJiang2015/RISeC (`data/train`, `data/dev`, `data/test`). The paper says it was annotated with BRAT; the file format was not viewed [U].
- **Licence** [V]: "MIT License", "Copyright (c) 2020 Yiwei Jiang". The recipes are SIMMR/CURD texts, whose upstream terms are UNVERIFIED.
- **Size** [V]: 260 recipes. Entity counts (Table 2): Food 3,232; Action 3,061; Tool 1,138; Condition clause 487; Duration 411; Temperature 381; Other 270; Purpose clause 147. There are 1,526 zero-anaphora verbs (ZAV), each with textual descriptions of the implicit argument. Relation counts (Table 3): Arg_PPT 3,196; Arg_GOL 557; Arg_DIR 91; Arg_PRD 74; Arg_PAG 25; ArgM_TMP 884; ArgM_LOC 515; ArgM_MNR 432; ArgM_PRP 137; ArgM_SIM 92; ArgM_INT 73.
- **Label set** [V]:
  - Entities: Action (+ZAV flag), Food (including "intermediate products (e.g., 'the meat mixture')"), Tool, Duration, Temperature, Other, Condition_Clause, Purpose_Clause.
  - Relations: PropBank-style Arg_* / ArgM_* (listed above).
- **Splits** [V]: "50% training, 20% development and 30% test sets, using the same splits as SIMMR".
- **Reported metrics** [V]:
  - Table 1, micro-F1 on the test set (GloVe / BERT-base / BERT-large): Entity 89.8 / 91.7 / **92.6**; ZAV 89.1 / 89.0 / **89.8**; Relation 65.5 / 67.1 / **67.5**.
  - Table 2 per entity (BERT-large F1): Food 94.2, Action 97.0, Tool 89.8, Condition clause 80.5, Duration 86.5, Temperature 88.4, Other 41.9, Purpose clause 67.2.
  - The seq2seq ZAV description generation "largely failed".
  - Agreement: no figure. Annotators were "in close communication during the entire annotation process".
- **Scope:** spans (including actions and intermediates), events (predicate–argument relations) and **implicit arguments (zero anaphora)**. It is a DAG, but without explicit state fields.
- **CPU:** unknown. The GloVe+BiLSTM span model is plausibly CPU-trainable on 130 training recipes (unmeasured). The paper's baseline code is not in the repo listing [U].
- **Cascade relevance:** **events and implicit-argument / coreference stages**, complementing ERFG. It is fully open (MIT).

### NERRES-12 — ARA (Aligned Recipe Actions; the name is correct)

- **Primary paper** [V]: L. Donatelli, T. Schmidt, D. Biswas, A. Köhn, F. Zhai, A. Koller. *Aligning Actions Across Recipe Graphs.* EMNLP 2021, pp. 6930–6942. https://aclanthology.org/2021.emnlp-main.554
- **Data URL** [V]: https://github.com/coli-saar/ara. "The data folder contains an updated version (ARA 1.1)".
- **Licence** [V]: README: "This work is licensed under a Creative Commons Attribution 4.0 International License". The repo also carries an Apache-2.0 LICENSE (sidebar: "Apache-2.0, CC-BY-4.0 licenses found").
- **Size** [V] (Table 3): 10 dishes; 110 recipes (11 per dish); 1,592 annotated action pairs; at least 3 crowd annotations per source action; 3–37 actions per recipe (mean 15.1). Recipes come from the Microsoft Research Multimodal Aligned Recipe Corpus (L'20).
- **Annotation** [V]: crowdsourced (Prolific, 250 participants). 190 of the 1,592 source actions were expert-adjudicated. Raw vote agreement with the plurality was 69.3%; human accuracy against gold was 79%.
- **Splits** [V]: 10-fold CV by dish (one dish held out).
- **Reported metrics** [V]:
  - Table 4, alignment accuracy: human upper bound 79.0; sequential 16.5; cosine 41.5; common action pairs 52.1; base model 66.3; **extended (graph-aware) 72.4**.
  - Tables 1–2, ERFG tagger/parser: tagger F1 89.6±0.3 (ELMo) / 88.5±0.2 (mBERT); parser F1 78.2±0.0 (gold tags) / 72.3±0.8 (end-to-end) versus Y'20's 71.1 / 43.3.
- **Scope:** actions only. Cross-recipe event alignment over parsed ERFG-style graphs. It is not an entity-NER dataset.
- **CPU:** unknown.
- **Cascade relevance:** a downstream **event-level** evaluation (are two recipes' events "the same step"?). Low priority for span NER, useful later for graph comparison.

### NERRES-13 — ingredient-parser (Python, CRF; NYT tagger lineage)

- **Canonical name:** `ingredient-parser` (GitHub strangetom/ingredient-parser); PyPI `ingredient-parser-nlp` **2.8.0, released 22 Sep 2026**, `Requires-Python >=3.11` [V]. Docs: https://ingredient-parser.readthedocs.io/en/latest/
- **Primary paper:** none (software).
- **Licence** [V]: GitHub "MIT license"; PyPI "MIT". **The licences of the training-data sources are not stated** [U]. allrecipes, bbc and cookstr come from the archive.org item `recipes-en-201706`; nyt comes from the NYTimes repo (Apache-2.0).
- **Model** [V]: "Condition Random Fields (CRF) model" via python-crfsuite. The sample trainer uses c1 = 0.2, c2 = 1.
- **Training data** [V] (labelled sentences): allrecipes 15,000; bbc 15,000; cookstr 15,000; manual 28; nyt 30,000; tc 6,318. That totals 81,346; the README says "over 81,000".
- **Labels** [V]: QTY, UNIT, SIZE, PREP, PURPOSE, PUNC, B_NAME_TOK, I_NAME_TOK, NAME_VAR, NAME_MOD, NAME_SEP, COMMENT, OTHER.
- **Splits** [V]: 80/20 via `train_test_split`, "stratified so each dataset is equally represented". Without `--seed` the seed is random but printed; the same `--seed` reproduces the split.
- **Reported metrics** [V] (README, "test data set of 20% of the total data"): **sentence-level accuracy 94.94%**; **word-level accuracy 98.03%**; micro P = R = F1 = 98.03%. This is **token-level**, not span-level.
- **CPU** [V]: **yes**. Training takes about 1 hour on a laptop ("Intel Core 15-10300H", 64 GB; "8 GB should be more than enough"; no GPU required).
- **Scope:** ingredient lines. Quantity, unit, size, preparation, purpose, name decomposition (variants, modifiers, separators) and comments. The output also includes `foundation_foods`, a weak linking signal.
- **Cascade relevance:** a production-grade, CPU-only **ingredient-line span and attribute baseline**, and a candidate silver labeller. Its token-level metrics need the shared scorer's token mode to be comparable.

### NERRES-14 — NYT ingredient-phrase-tagger (lineage)

- **URL** [V]: https://github.com/nytimes/ingredient-phrase-tagger. "This repository was archived by the owner on Mar 6, 2019. It is now read-only."
- **Licence** [V]: "Apache 2.0".
- **Model and data** [V]: a CRF trained with CRF++, with a snapshot of "roughly 180k examples" from the NYT cooking database. Tags shown are B-QTY, B-UNIT, B-NAME, I-NAME; the JSON fields are qty, unit, name, other, comment.
- **Metrics:** none reported in the README. The NYT blog posts (2015, 2016) are linked but were not opened [U].
- **CPU:** yes (CRF++; "roughly 30 minutes for 130k examples" on a 2012 MacBook Pro [V]).
- **Cascade relevance:** historical baseline and the data source for ingredient-parser's `nyt` portion. It is superseded by NERRES-13.

### NERRES-15 — DeBERTa-v3 + CRF for recipe / ingredient NER

- **Result: NOT FOUND.** No published recipe or ingredient NER work using DeBERTa-v3 + CRF was found (extended web search).
- **Closest verified items:**
  - RecipeDB3 uses `microsoft/deberta-base` (**v1**), **no CRF** (NERRES-03).
  - TASTEset reports "BERT with CRF" (BERT, not DeBERTa), All 0.929±0.008 (NERRES-04).
  - GLiNER uses a DeBERTa-v3 backbone but a span-matching head, not a CRF (NERRES-16).
  - DeBERTa-v3+CRF exists in other domains (e.g. an NL4Opt shared-task system, arXiv:2212.07219). That is seen in search snippets only and was **not opened** [U].
- **Implication:** a DeBERTa-v3(-small/-xsmall)+CRF ingredient/instruction tagger would be a **new baseline** for this project, not a reproduction. Its CPU feasibility is unknown; xsmall/small are the only plausible CPU sizes.

### NERRES-16 — GLiNER (zero-shot / open-type NER)

- **Primary paper** [V]: U. Zaratiana, N. Tomeh, P. Holat, T. Charnois. *GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer.* NAACL 2024 (Long), pp. 5364–5376. DOI 10.18653/v1/2024.naacl-long.300. Also arXiv:2311.08526 (v1, 14 Nov 2023, "Work in progress").
- **Code** [V]: https://github.com/urchade/GLiNER ("Apache-2.0 license"). The README says GLiNER is "optimized to run on CPUs and consumer hardware", with ONNX export, FP16, and INT8 (QAT advised).
- **Model licences** [V] (HF version table): **v2 and v2.1 (small 166M, medium 209M, large 459M, multi 209M) = apache-2.0**. **v0 (gliner_base, gliner_multi) and v1 = cc-by-nc-4.0.** v2.1 was trained on `urchade/pile-mistral-v0.1`. The paper's models used Pile-NER (44,889 passages, about 240k spans, 13k types).
- **Reported metrics** [V], Table 1 (zero-shot out-of-domain; exact-match F1): GLiNER-L **60.9** average (AI 57.2, Literature 64.4, Music 69.6, Politics 72.6, Science 62.6, MIT Movie 57.2, MIT Restaurant 42.9); GLiNER-M 55.4; GLiNER-S 52.7; ChatGPT 47.5; UniNER-13B 55.6. Param counts in the paper's table (50M / 90M / 0.3B) differ from the HF table (166M / 209M / 459M); the counting basis is not stated.
- **Recipe/food evaluation:** **none found.**
- **CPU:** **yes** (vendor claim plus small sizes).
- **Cascade relevance:** a zero-shot **span** floor for new or rare labels (e.g. TOOL_STATE, PREPROCESS) and a pre-annotation aid. **Do not** use it for gold pre-fill (the gold rules forbid model pre-fill).

### NERRES-17 — GLiNER2 / GLiNER2.5

- **Paper** [C]: U. Zaratiana, G. Pasternak, O. Boyd, G. Hurn-Maloney, A. Lewis. *GLiNER2: An Efficient Multi-Task Information Extraction System with Schema-Driven Interface.* arXiv:2507.18546 (24 Jul 2025). Also reported as EMNLP 2025 System Demonstrations (2025.emnlp-demos.10). Both come from search results; **the paper pages were not opened** [U].
- **Code** [V]: https://github.com/fastino-ai/GLiNER2 ("This project is licensed under the Apache License 2.0").
- **Models** [V] (sizes from the repo page): gliner2-base-v1 205M, gliner2-large-v1 340M, gliner2-multi-v1 ~205M, gliner2.5-small-v1 74M, gliner2.5-base-v1 194M, gliner2.5-multi-v1 287M. **Per-model licences are not stated on the repo page** [U].
- **Metrics:** not read [U]. **Recipe evaluation:** none found.
- **CPU:** claimed ("CPU first … no GPU required") [V].
- **Cascade relevance:** schema-driven extraction (entities plus classification plus structured fields). This could prototype attribute filling, but it is unproven on recipes.

### NERRES-18 — kNN-NER / retrieval-augmented NER (recipe application: NOT FOUND)

- **Primary paper** [V]: S. Wang, X. Li, Y. Meng, T. Zhang, R. Ouyang, J. Li, G. Wang. *kNN-NER: Named Entity Recognition with Nearest Neighbor Search.* arXiv:2203.17103 (31 Mar 2022, "Preprint"). Code: https://github.com/ShannonAI/KNN-NER ; the licence was not checked [U].
- **Method** [V]: retrieve the k nearest training tokens and interpolate their label distribution with the base tagger. "No extra training". It reports Weibo F1 72.03 (+1.25) and matches vanilla performance "using 40% less training data".
- **Recipe/food application:** **none found** (extended search). Adjacent work seen only in search snippets [U]: GPT-NER (arXiv:2304.10428; entity-level retrieval of demonstrations) and FoodSEM (arXiv:2509.22125; food entity *linking* LLM, RAG listed as future work).
- **CPU:** unknown. The datastore lookup is CPU-friendly, but the base tagger cost dominates.
- **Cascade relevance:** a candidate fix for the RecipeDB3 weak long-tail labels (PREPROCESS 0.50, QUANTITY 0.638). It would be a new experiment, not a reproduction.

### Adjacent resources seen but not carded

FINER (Komariah & Sin 2022, *Applied Sciences* 12(20):10310) and FoodBase (Popovski et al. 2019) are part of Ibrahim et al.'s 7-benchmark suite. They are verified only as cited there [C]. Their licences and data URLs were not checked [U].

---

## Licence summary

| Status | Resources | What it means for us |
|---|---|---|
| **No licence stated (permission needed)** | NERRES-01 `recipe-knowledge-mining`, NERRES-03 `RecipeDB3_NER_Research_Paper`, NERRES-10 ERFG (email access) | Default all-rights-reserved. Needs written permission. The CoSyLab ask is already drafted (A2.3 email, item 6); ERFG needs an email to Yamakata. |
| **Unresolved** | NERRES-02 (Goel data link), NERRES-09 JFC-Recipe (paper says CC BY-NC 4.0, repo says CC BY-SA 4.0; recipe texts need Cookpad via NII-IDR) | Ask the authors; do not redistribute meanwhile. |
| **Non-commercial** | NERRES-06/07/08 (CC BY-NC 4.0), RecipeDB website (CC BY-NC-SA 3.0), GLiNER v0/v1 (CC BY-NC 4.0) | Fine for academic research only. ShareAlike (RecipeDB) propagates to derivatives. |
| **Permissive** | NERRES-04, NERRES-05 (MIT on GitHub; the IEEE DataPort copy is subscription), NERRES-11 (MIT), NERRES-12 (CC BY 4.0 data), NERRES-13 (MIT), NERRES-14 (Apache-2.0), NERRES-16 v2/v2.1 (Apache-2.0), NERRES-17 code (Apache-2.0) | Usable. Upstream recipe-text rights for scraped corpora remain UNVERIFIED for every dataset: TASTEset sites, SIMMR, Allrecipes UK, RecipeNLG. |

---

## Recommended first reproductions on CPU (max 3)

The selection criteria were: (a) a published number with a fully specified setting I could read; (b) documented or structurally evident CPU feasibility; (c) direct relevance to the project's span stage on RecipeDB-style text; (d) a known licence path.

1. **RecipeDB3 instruction NER (NERRES-03), spaCy blank `en`.**
   - **Target:** micro-F1 **0.9258** and macro-F1 **0.8698** with seqeval; per-label figures as in the card.
   - **Setting:** `train_test_split(test_size=0.2, random_state=42)` after dropping token/tag-length-mismatched rows; 10 iterations; minibatch 8; dropout 0.3.
   - **Why:** it is the project's own B08 target and covers 12 instruction labels including ACTION and UTENSIL. It has no transformer, so it is CPU-cheap. It exposes the weak labels the project wants to beat.
   - **Gate:** the repo has **no licence**, so it needs Bagler's permission (H1/H2) before any download. Also confirm that `Instructions_Annotated_Dataset.csv` equals the notebook's `RecipeDB3_BIO.csv`.
   - **Done-check:** each of micro, macro and every per-label F1 within ±0.01 of the notebook, or a documented reason why not (spaCy version, non-determinism).

2. **Legacy RecipeDB ingredient NER with a CRF (NERRES-01/02): Stanford NER on the AR/GK train/test TSVs.**
   - **Target:** Diwan Table IV Both→Both **0.9611**, AR→AR **0.9682** and GK→GK **0.9519**. Goel's reproduction got 95.52 / 96.82 / 95.16.
   - **Why:** it is *already known to reproduce* (Goel matched 7/9 cells exactly and the rest within <1%), and it runs on "an 8 GB CPU RAM system". That makes it the ideal **scorer sanity check** before any new model. It also provides the "RecipeDB 7 tags" adapter.
   - **Gate:** the repo has no licence (same permission request). The Stanford NER software licence is UNVERIFIED and must be checked before install. Check that the TSV counts equal 6,612 / 2,188.
   - **Done-check:** all 9 Table IV cells within ±0.01.

3. **ingredient-parser CRF (NERRES-13).**
   - **Target:** **sentence accuracy 94.94%, word accuracy 98.03%** on a 20% stratified hold-out, with a fixed `--seed`.
   - **Why:** CPU-only by design (about 1 h, no GPU, documented). The code is MIT and the split is controlled by a seed. It is the strongest ingredient-line CRF in the NYT lineage and **can start without waiting for H1**. It also exercises the scorer's token-level and sentence-level modes, and gives a ready silver labeller for ingredient lines.
   - **Gate:** the licences of its training-data sources (archive.org scrape) are UNVERIFIED. Use the data only for reproduction, not redistribution, until they are checked.
   - **Done-check:** both accuracies within ±0.5 points across 3 seeds.

**Next after these (not in the top 3):** TASTEset v1 BERT-base-cased 5-fold (All 0.932±0.008; MIT). Run a one-fold CPU timing probe first; its CPU feasibility is "unknown". Then ERFG BERT-NER 87.6, once Yamakata grants access.

---

## Common scorer requirements

The numbers above were produced with at least six incompatible protocols:

| Source | Scorer and protocol |
|---|---|
| TASTEset | nervaluate strict, 5-fold CV |
| RecipeDB3 | seqeval default, random 80/20, test-set model selection |
| Goel | macro-F1 over tags, fixed 2,187 test |
| ERFG | 10-fold CV |
| Ibrahim KA | per-entity-type passes, own re-splits, "token-level … strict span" |
| ingredient-parser | token and sentence accuracy |

A shared scorer must make these comparable.

1. **Canonical input.** Raw text plus **character offsets** for gold and predictions. It must support:
   - **discontinuous spans** (TASTEset BRAT, ERFG Ac2 / ReciFine ACTION_BY_CHEF_DISCONTINUOUS);
   - **nested/overlapping spans** (declare per corpus whether they are allowed);
   - lossless BIO/IOB2 ↔ span conversion, with an explicit rule for ill-formed `I-` starts.
   - Reject offsets computed on normalised text (Diwan lowercases, lemmatises and drops stop-words), or re-anchor them first.
2. **Matching modes, all reported:**
   - **strict** (exact boundary and type);
   - **exact boundary** (type ignored);
   - **partial overlap**;
   - **type with overlap**.
   These are the nervaluate schemas. Also report **seqeval default (conlleval-compatible)** and **seqeval strict IOB2** separately, because they differ on ill-formed chunks. Report token-level accuracy/P/R/F1 and **sentence-level exact accuracy** only as secondary metrics (ingredient-parser style).
3. **Averaging, all reported:** per-label P/R/F1 with support, plus **micro, macro and weighted** averages. "All" must name which one it is. List any **excluded labels**, e.g. TASTEset 2.0 drops EXCLUDED / EXCLUSIVE / POSSIBLE SUBSTITUTE, and RecipeDB3 maps SIZE → O. Excluded labels must be reported, not silently dropped.
4. **Label mapping.**
   - Version a mapping table per corpus to the project schema, with its hash recorded in the output.
   - Report **native-label scores and mapped-label scores** side by side.
   - Make many-to-one and split cases explicit: ERFG `Q` = number + unit, whereas TASTEset, RecipeDB and Goel have separate QUANTITY and UNIT; NAME / ingredient / FOOD → INGREDIENT.
   - Unmappable labels go to an explicit `UNMAPPED` bucket.
5. **Tokenisation independence.** Score on characters (spans), never on subword tokens.
   - Models labelling first sub-tokens only (RecipeDB3: −100 on continuations) must be projected back to word and character spans before scoring.
   - Record the tokenizer and version used for any token-level metric.
6. **Splits and leakage.**
   - Use published split files or seeds (Diwan TSVs; RecipeDB3 `random_state` 48 and 42; RISeC train/dev/test; ingredient-parser `--seed`).
   - Store a split manifest (ids and hash) next to each result.
   - Model selection must happen on a dev set. Flag any result selected on test (RecipeDB3 ingredient).
   - Run a duplicate / near-duplicate audit (exact and number-masked) across train and test. This is mandatory for augmented sets (Goel LwTR / SR / SiS).
7. **Per-type decomposition.** For entity-type-specific models (Ibrahim KA), merge the per-type predictions into one span set and resolve overlaps with a declared rule, then score jointly. Per-type scores are reported as well, not instead.
8. **Variance.** CV folds or seeds give mean ± sd (TASTEset 5-fold; KA 10 seeds). Add bootstrap 95% CIs over documents for single-split results.
9. **Beyond spans (later stages, same harness):**
   - edge P/R/F1 with **gold nodes and with predicted nodes** (ERFG Table 5 convention);
   - relation micro-F1 (RISeC);
   - zero-anaphora detection F1;
   - linking accuracy and macro-F1 over KB IDs (JFC);
   - quantity accuracy with a numeric tolerance (JFC uses 0.01);
   - alignment accuracy (ARA).
10. **Provenance in every result row:** scorer version, mode, mapping hash, split hash, model checkpoint id, seed and hardware. "Cross-protocol SOTA" comparisons (e.g. KA's SOTA column) must be labelled as such and never treated as like-for-like.

---

## Sources

Primary sources were opened today unless marked [C].

1. Diwan, Batra, Bagler 2020 — https://arxiv.org/abs/2004.12184 (PDF read in full) ; repo https://github.com/cosylabiiit/recipe-knowledge-mining
2. Goel et al. 2024 — https://aclanthology.org/2024.lrec-main.406/ (PDF pp. 1–9 read) ; https://arxiv.org/abs/2402.17447
3. RecipeDB3 NER repo — https://github.com/cosylabiiit/RecipeDB3_NER_Research_Paper ; tree and metadata via api.github.com ; notebooks read via raw.githubusercontent.com (code and outputs, no data)
4. RecipeDB website licence — https://cosylab.iiitd.edu.in/recipedb/
5. TASTEset — https://arxiv.org/abs/2204.07775 ; https://ar5iv.arxiv.org/html/2204.07775 ; https://github.com/taisti/TASTEset (LICENSE read)
6. TASTEset 2.0 — https://github.com/taisti/TASTEset-2.0 ; https://ieee-dataport.org/node/10391 ; K-CAP '23 record [C] https://sin.put.poznan.pl/publications/details/i56237 (bot-blocked)
7. ReciFine — https://aclanthology.org/2026.findings-eacl.210/ (PDF pp. 1–6 read) ; https://github.com/nuhu-ibrahim/ReciFine ; https://huggingface.co/datasets/nuhuibrahim/recifinegold ; https://huggingface.co/datasets/nuhuibrahim/recifine ; https://huggingface.co/collections/nuhuibrahim/recifine ; https://huggingface.co/nuhuibrahim/recifinegold-reciperoberta-ka-question
8. Ibrahim, Stevens, Batista-Navarro 2026 — https://aclanthology.org/2026.eacl-long.127 (PDF pp. 1–7, 9–13 read)
9. JFC-Recipe — https://aclanthology.org/2026.lrec-1.504/ (PDF pp. 1–10 read) ; https://github.com/ku-lsta/JFC-Recipe (LICENSE read)
10. ERFG — https://aclanthology.org/2020.lrec-1.638 (PDF read in full) ; https://sites.google.com/view/yy-lab/resource/english-recipe-flowgraph
11. RISeC — https://aclanthology.org/2020.aacl-main.82 (PDF read in full) ; https://github.com/YiweiJiang2015/RISeC (LICENSE read)
12. ARA — https://aclanthology.org/2021.emnlp-main.554 (PDF pp. 1–8 read) ; https://github.com/coli-saar/ara
13. ingredient-parser — https://github.com/strangetom/ingredient-parser ; https://pypi.org/project/ingredient-parser-nlp/ ; docs `explanation/data.html` and `explanation/training.html`
14. NYT tagger — https://github.com/nytimes/ingredient-phrase-tagger
15. GLiNER — https://aclanthology.org/2024.naacl-long.300/ ; https://arxiv.org/abs/2311.08526 ; https://ar5iv.arxiv.org/html/2311.08526 ; https://github.com/urchade/GLiNER ; https://huggingface.co/urchade/gliner_small-v2.1 ; https://huggingface.co/urchade/gliner_medium-v2.1
16. GLiNER2 — https://github.com/fastino-ai/GLiNER2 ; paper [C] https://arxiv.org/abs/2507.18546
17. kNN-NER — https://arxiv.org/abs/2203.17103
18. RecipeBERT (unrelated recommender) — https://zenodo.org/records/14041762
19. Scorers — https://github.com/chakki-works/seqeval ; https://github.com/MantisAI/nervaluate

**Queries tried:**
- "Diwan Batra Bagler named entity based approach"
- "RecipeDB 3.0 / RecipeDB3" (standard and extended)
- "ReciFineGold" (exact)
- "TASTEset … Wróblewska"
- "TASTEset 2.0 / K-CAP 2023 … doi"
- "Deep Learning Based NER Models for Recipes"
- "English Recipe Flow Graph corpus download licence"
- "JFC-Recipe"
- "ARA recipe dataset"
- "RecipeBERT huggingface" / "RecipeBERT paper"
- "DeBERTa-v3 CRF recipe ingredient NER" (extended)
- "retrieval-augmented / kNN NER recipes food" (extended)
- "GLiNER zero-shot food recipe"
- "GLiNER2 … arXiv"
- "Ibrahim Batista-Navarro EACL 2026 knowledge-augmented"

**Not done (needs approval):** no dataset, model or notebook was downloaded or executed. Row counts, duplicate rates and file-to-notebook equivalence for NERRES-01/02/03 therefore remain UNVERIFIED.
