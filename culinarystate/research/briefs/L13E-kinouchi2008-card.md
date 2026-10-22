# L13E — Kinouchi et al. 2008: source card and reproduction card

> **Pointer:** the arXiv preprint (SNAP-L13E-0002) is checked against A1–A27 in **§10** (appended; §7–§9 were already taken). It conflicts with this version on eq. (1), β, α and the A27 relation.

| Lane | Block | Source | Date | Session |
|---|---|---|---|---|
| C (L13E), feeds B15 step 2 | SSOT §261.18 item 1 | SNAP-L13E-0001 / SRC-L13E-KINOUCHI2008 | 2026-10-08 | Parv + Claude (H2 extension, approved by Parv 2026-10-08 per session instruction) |

**Status:** TRANSCRIBED from the publisher PDF. **Every number below was copied from the paper by a machine and
must be spot-checked by a human against `data/raw/l13e/kinouchi2008_njp-wayback.pdf` before use** (checklist in §9).
Nothing in this card comes from secondary summaries. Values marked *(ours)* are our own arithmetic or figure
readings. Items marked **[GUESS]** are reimplementation choices the paper does not specify.

**Page convention.** "p. N" means the article page number printed in the page header (p. 1 has no printed number).
The PDF has one extra IOP cover page, so **PDF page = p. N + 1**.

> **Approval and sourcing:**
> - H2 was approved by Parv on 2026-10-08 (**DEC-035**). The sourcing is recorded in **DEC-037**: the publisher's PDF comes from an Internet Archive capture, because iopscience disallows all automated agents in robots.txt; the author preprint comes from arxiv.org.
> - Both PDFs are local-only, with no redistribution.
> - The preprint was fetched later (SNAP-L13E-0002), so the "not downloaded" lines in §2 and §8 are superseded. The comparison is in §10.

---

## 1. Verified citation

| Field | Value | Verified against |
|---|---|---|
| Authors | Osame Kinouchi, Rosa W Diez-Garcia, Adriano J Holanda, Pedro Zambianchi, Antonio C Roque (corresponding author: Roque) | PDF p. 1; Crossref; landing page `citation_author` meta |
| Title | The non-equilibrium nature of culinary evolution | PDF p. 1; Crossref |
| Journal | New Journal of Physics **10** (2008) 073020 (8pp), issue 7 | PDF p. 1 ("New Journal of Physics 10 (2008) 073020 (8pp)"); Crossref (vol 10, issue 7, page 073020) |
| Dates | Received 2 April 2008; Published 10 July 2008 | PDF p. 1; landing page |
| DOI | 10.1088/1367-2630/10/7/073020 | PDF p. 1; Crossref; doi.org handle API |
| Landing URL | https://iopscience.iop.org/article/10.1088/1367-2630/10/7/073020 (DOI target per doi.org handle API) | doi.org handle record |
| Recommended citation | Kinouchi O, Diez-Garcia R W, Holanda A J, Zambianchi P and Roque A C 2008 The non-equilibrium nature of culinary evolution *New J. Phys.* **10** 073020 | |

Note: the article has 8 pages and an article number (073020), not a page range.

## 2. Snapshot, access route and licence

| Field | Value |
|---|---|
| Snapshot | `SNAP-L13E-0001` in `ledgers/snapshots/l13e_snapshots.jsonl` |
| Local file | `data/raw/l13e/kinouchi2008_njp-wayback.pdf` |
| sha256 | `98db4d2b4a766f07ed32542c1724f4d8c2cea5d73c7ccbd46d4061263304afcc` |
| Bytes | 1,461,489 (9 PDF pages = 1 IOP cover page + 8 article pages) |
| Retrieved (UTC) | 2026-10-08T18:10:46Z |
| Fetched URL | https://web.archive.org/web/20240420175153id_/https://iopscience.iop.org/article/10.1088/1367-2630/10/7/073020/pdf |
| Version | **Publisher version of record** (IOP typeset PDF; creation date 9 Jul 2008, re-stamped by IOP's server at download on 20 Apr 2024) |

**Access route.**

1. `iopscience.iop.org/robots.txt` (checked 2026-10-08) ends with `user-agent: *` / `Disallow: /`. No automated
   request was therefore sent to iopscience for the landing page or the PDF.
2. Instead, the publisher PDF was taken from the Internet Archive Wayback Machine capture of the publisher's own PDF
   URL: memento 2024-04-20T17:51:53Z, ArchiveTeam crawl, original bytes via the `id_` flag.
   `web.archive.org/robots.txt` returns 404.
3. The IOP cover page says "This content was downloaded from IP address 37.120.189.199 on 20/04/2024 at 18:51".
   This is the archiver's address, which IOP stamps on every download. A copy a human downloads directly will
   therefore have a different sha256, but the 8 article pages should be identical.
4. arXiv:0802.4393v1 also exists (see §8). It was **not** downloaded.

**Licence as actually stated (quoted):**

- PDF cover page: "OPEN ACCESS".
- Article p. 1 masthead: "New Journal of Physics The open–access journal for physics".
- Article p. 1 footer: "© IOP Publishing Ltd and Deutsche Physikalische Gesellschaft".
- Publisher landing page (Wayback capture 20240204062520): "The following article is Open access" … "Published under
  licence by IOP Publishing Ltd".

**No Creative Commons licence is named on either the PDF or the landing page.** OpenAlex metadata lists `cc-by` for
the publisher location; this is secondary and **unverified**. Crossref has no licence element.

Treat the paper as free to read and cite. Do not redistribute the PDF outside the project until a human confirms the
licence (for example, from the current iopscience page in a browser).

## 3. Datasets (empirical side)

All quoted from p. 2 unless noted.

**Corpus.** "The culinary corpus considered by us consists of four different cookery books: the Brazilian Dona Benta
[17], the French Larousse Gastronomique [18], the British New Penguin Cookery Book [19] and the medieval Pleyn Delit
[20]. We have constructed a database for each one of them containing its entire population of recipes and
ingredients. The only exception is the database for the French cookery book, which contains a random sample (40%) of
the whole population of recipes. To examine temporal effects, we have considered three very different editions of
Dona Benta [17] (1946, 1969 and 2004) …" (p. 2)

**Table 1** (p. 2), "Numerical characteristics for the considered cookery books":

| Cookery book | No. of recipes | No. of ingredients | Average recipe size |
|---|---|---|---|
| Dona Benta (1946) | 1786 | 491 | 6.7 |
| Dona Benta (1969) | 1894 | 657 | 7.1 |
| Dona Benta (2004) | 1564 | 533 | 7.4 |
| Larousse Gastronomique (2004)ᵃ | 1200 | 1005 | 10.8 |
| New Penguin Cookery Book (2001) | 878 | 489 | 9.5 |
| Pleyn Delit (Medieval) | 380 | 219 | 9.7 |

ᵃ "Recipes have been sampled. The total number of recipes is above 3000."

**Editions, from the references (p. 8).**

- [17] Dona Benta: Comer Bem 1946 26th edn; 1969 51st edn Revised; 2004 76th edn Revised (São Paulo: Companhia
  Editora Nacional).
- [18] Larousse Gastronomique 2004 (Paris: Larousse).
- [19] Norman J 2004 The New Penguin Cookery Book (London: Penguin).
- [20] Hieatt C B, Hosington B and Butler S 1996 Pleyn Delit: Medieval Cookery for Modern Cooks 2nd edn (Toronto:
  University of Toronto Press).

**Preprocessing actually described:**

- "For each cookery book database, we counted the number of recipes in which each ingredient appears. The ingredients
  were ordered according to descending frequency of usage." (p. 2)
- "The ingredient usage frequency f (r ) is the relative number of recipes that use the ingredient with rank r." (p. 3)
- The scope is restricted to recipe–ingredient incidence: "we examine only a particular aspect of cookery books,
  namely the relationship between its recipes and ingredients, and neglect for the moment the very important role
  played by culinary preparations" (p. 2).

**Not described:** ingredient-name normalisation, quantities, how sub-recipes or garnishes were treated, or how the
40% Larousse sample was drawn. The paper has **no data or code availability statement**, so the cookbook databases
are not available. Gaps A23 and A24 are listed in §6.

## 4. Reported empirical results (quoted exactly)

**E1. Rank–frequency law, eq. (1), p. 2.** "All these curves exhibit a power-law behaviour which can be well fitted by
a Zipf–Mandelbrot law [22, 23] with an exponential cut-off [24] to capture finite size effects,"

  f(r) = C / (a + r)^β · exp(−r/r_c)        (1)   *(transcribed from the rendered equation)*

**E2. Fitted values, p. 3.** "The best fit exponent β ≅ 1.31 worked reasonably well for all curves (the other
parameters are C = 8.7, a = 6.4 and r_c = 800)". No uncertainty, fit method or fit range is given.

- *(ours)* With these values, eq. (1) gives f(1) = 0.631, f(10) = 0.220, f(100) = 0.0170 and f(500) = 0.00133. So
  f(1) ≈ 0.6 matches Fig. 3's first point, consistent with f being a *fraction of recipes*.

**E3. Figure 1 (p. 3), frequency–rank plots, log–log.**

- (a) "Cultural invariance": Pleyn Delit, Dona Benta 1969, New Penguin, Larousse.
- (b) "Temporal invariance": Dona Benta 1946, 1969, 2004.
- No numbers beyond E2 are given.

**E4. Ingredient degree distribution, p. 3.** "Plots of the degree distribution for the ingredients of the cookery
books show that they are right-skewed with a two-decade power law region well fitted by P^I(k) ∝ k^−α with α ≅ 1.73.
This value has been found by a fit proportional to k^−(α−1) of the complementary cumulative distribution (figure 2),"

  P_C(k) = 1 − Σ_k P^I(k)        (2)   *(summation limits as printed; see A16)*

"which gives the probability that an ingredient is used in more than k recipes. It is compatible with the relation
α = 1 + 1/β valid for pure power laws present in rank plots and degree distributions [11]. This anomalous exponent
cannot be obtained from a general Yule process [8] since in this latter case α ⩾ 2." (pp. 3–4)

- *(ours)* 1 + 1/1.31 = 1.763.

**E5. Figure 2 (p. 4).** "Complementary cumulative degree distribution P_C(k) for ingredients with power law fitting
k^−0.73 (solid line). Inset: degree distribution P^R(j) for French recipes."

- The cookery book used for the main panel is not named (A15).
- The inset's y-axis runs 0–100, i.e. counts *(ours, figure reading)*.

**E6. Recipe size, p. 4.** P^R(j) is "the probability distribution … that a randomly chosen recipe has j ingredients
(what we will call the size j of the recipe)". Averages are in Table 1.

**E7. Founder effect.** The paper reports **no numerical founder-effect statistic**. Evidence is qualitative only:
Fig. 5 (p. 7) and the text on p. 6 (quoted in §5.5).

## 5. The copy–mutate model, exactly as defined

### 5.1 Verbatim definition

**p. 4:** "On the basis that culinary recipes are examples of cultural replicators, or 'memes' [25, 26], we propose a
copy-mutate algorithm to model culinary evolution as a branching process (figure 3 inset). Our attempts to fit all the
frequency distributions have shown that our model needs at least five parameters to work: the number T of
generations (iterations or 'time') until the process is halted, the number K of ingredients per recipe (where K is
compared to the average number ⟨K⟩ of the cookery book), the number L(≠ K) of ingredients ('loci') in each recipe to
be mutated, the number R0 of initial recipes in the cuisine and M, the ratio between the sizes of the pool of
ingredients and the pool of recipes. Hence, starting with t0 = R0, at each time step there are R(t) = t recipes and
MR(t) ingredients available to be used."

**p. 4:** "We tried models without the concept of fitness, with no success. So, the present model ascribes to each
ingredient i a random fitness f_i with values uniformly distributed in the interval [0,1]. … At each iteration, we
randomly chose a recipe (a 'mother') and copied it. Within this copy, we randomly chose an ingredient (with fitness
f_i) to be compared with an ingredient also randomly chosen from the ingredients pool: if f_j > f_i, where f_j is the
fitness of the ingredient from the pool, we replace ingredient i by ingredient j."

**p. 5:** "This process is repeated L times, thus generating a 'daughter' recipe that is added to the recipes pool (it
is possible that the daughter remains identical to the mother, which we interpret as a new recipe that differs from
the previous one in the cooking procedures but not in their ingredients). Finally, at each time step, new ingredients
are introduced in the ingredients pool to maintain the ratio M fixed."

**Fig. 3 caption (p. 5):** "At each time step, a randomly chosen 'mother' recipe generates a mutated daughter recipe.
Notice that there is no recipe extinction."

**p. 5, contextual fitness (described, not used in any reported result as far as the text says):** "A more general
fitness function could be used, f_i^I = f_i + Σ_j f_ij + Σ_{j,k} f_ijk + ⋯ , to account for higher order interactions
between ingredients".

**p. 5, observables:** "We also define the fitness of the kth recipe as F^(k) = (1/K) Σ_{i=1}^{K} f_i and a total
time-dependent cuisine fitness F_Total(R(t)) = (1/R(t)) Σ_{k=1}^{R(t)} F^(k)." *(Formulas transcribed from the rendered
page; text extraction garbles them.)*

**p. 6:** "the branching ratio is σ = R(t + 1)/R(t) ≅ 1 = σ_c."

### 5.2 Variables (paper's symbols)

| Symbol | Paper's definition (p. 4–5) | Role |
|---|---|---|
| T | "number T of generations (iterations or 'time') until the process is halted"; also "the number of recipes is R = T = 1200" (p. 5) | stopping rule |
| K | "number K of ingredients per recipe (where K is compared to the average number ⟨K⟩ of the cookery book)" | recipe size (fixed) |
| L | "number L(≠ K) of ingredients ('loci') in each recipe to be mutated"; "the mutation rate L" (p. 5) | mutation attempts per daughter |
| R0 | "number R0 of initial recipes in the cuisine"; "(or independent 'phylogenetic trees')" (p. 5) | initial condition |
| M | "the ratio between the sizes of the pool of ingredients and the pool of recipes"; "the growth rate M of the ingredients pool" (p. 5) | pool size = M·R(t) |
| t, t0 | "starting with t0 = R0" | time = number of recipes |
| R(t) | "R(t) = t recipes" | recipe count |
| f_i | "random fitness f_i with values uniformly distributed in the interval [0,1]" | ingredient fitness |
| F^(k), F_Total | see §5.1 | observables (Fig. 4) |
| σ | "R(t + 1)/R(t) ≅ 1" | branching ratio |

**Parameter count.** The paper names **five** parameters: (T, K, L, M, R0). T and K are pinned to the data (R = T
recipes; K ≈ ⟨K⟩), so "the effective free parameters are only the initial number of recipes R0 …, the mutation rate L
and the growth rate M of the ingredients pool, which are not determinable from empirical data" (p. 5). That gives
**3 effective free parameters**.

The fitness law U[0,1] is fixed, not fitted. A sixth reported setting, used only for Fig. 3, is the 5-run average.

### 5.3 Restated algorithm (paper's symbols; unspecified choices flagged)

```
Initial condition (t = t0 = R0):
  ingredient pool P with |P| = M·R0 ingredients, each with f ~ U[0,1]          [A2: implied by "MR(t)"]
  R0 recipes, each a list of K ingredients                                       [GUESS — A1: how built?]
For t = R0, R0+1, …, until R(t) = T:                                             [A3: T = final recipe count]
  1. pick mother m uniformly at random from the R(t) existing recipes            [A9: "randomly" = uniform?]
  2. d ← copy(m)
  3. repeat L times:                                                             [A4: loci with/without replacement]
       choose a position (ingredient i, fitness f_i) uniformly in d
       choose ingredient j uniformly at random from the pool P                   [A5: whole pool incl. unused]
       if f_j > f_i: replace i by j in d                                         [A6: if j already in d?]
  4. append d to the recipe pool  →  R(t+1) = t + 1 (no recipe extinction)
  5. add new ingredients (f ~ U[0,1]) so that |P| = M·R(t+1), i.e. M per step   [A8: order, non-integer M]
Stop when R = T. Output: the T recipes (including the R0 initial ones)           [A12]
```

The acceptance rule is strict (f_j > f_i), and it is the only selection mechanism. Mutation is not forced: a daughter
can be identical to its mother.

### 5.4 Parameter values per figure

| Figure | Content | Parameters stated | Runs |
|---|---|---|---|
| Fig. 1 (p. 3) | empirical rank–frequency, 6 cookery books | eq. (1): β ≅ 1.31, C = 8.7, a = 6.4, r_c = 800 ("for all curves", see A14) | — |
| Fig. 2 (p. 4) | empirical CCDF P_C(k), plus inset P^R(j) for French recipes | fit k^−0.73, i.e. α ≅ 1.73 | — |
| Fig. 3 (p. 5) | Larousse data, Zipf–Mandelbrot fit and model | "T = 1200, K = 11, L = 4, M = 3 and R0 = 20" (p. 5) | "average of five runs" |
| Fig. 4 (p. 6) | 1 − F_total vs t, log–log | γ = 0.1; **model parameters not stated** | not stated |
| Fig. 5 (p. 7) | ingredient fitness vs rank r | **parameters not stated** | not stated (looks like a single run, with about 1100 ranked points *(ours)*) |

### 5.5 Model results, quoted

- **Fig. 3 / p. 5:** "They show a good agreement with the actual values of the Larousse database, since the number of
  recipes is R = T = 1200 = R_Larousse and K = 11 ≅ ⟨K⟩_Larousse = 10.8." Also: "Parameter fitting also gives a good
  agreement with the curves and values for all the other cookery books considered." The parameters for the other
  books are **not given**.
- **Fig. 4 / p. 6:** "1 − F_Total(t), which shows a very slow convergence to equilibrium in the form of a power law
  1 − F_Total(t) ∝ t^−γ, with γ = 0.1." Caption: "The rising phase is due to the initial copy of low fitness recipes,
  which lowers the overall culinary fitness F_total."
- **Founder effect / p. 6:** "the small number R0 of initial recipes plays the role of a 'founder' population. As a
  consequence, some low fitness ingredients present in the initial R0 recipes have a strong difficulty of being
  replaced and can even propagate during culinary growth."
- **Fig. 5 caption (p. 7):** "Observe the founder effect for some well ranked ingredients with small fitness (bottom
  left) and the overall average high fitness due to selective pressure. Notice also that there are several high
  fitness ingredients with poor ranking (upper right) due to the strong non-equilibrium character of the evolutionary
  process."
- **Ablation / p. 6:** "ingredient competition due to differential fitness is essential to obtain good modelling for
  rank values in the interval r = 1, …, KR0. We tested an algorithm without fitness selection and observed that the
  conservation of the first KR0 ingredients is so strong that they remain over represented in the population."

## 6. Ambiguities and under-specified details (a reimplementation must guess these)

**Model**

- **A1. Initial recipes.** How the R0 initial recipes are built is never stated: which ingredients, whether they are
  distinct within or across recipes, and whether founder fitnesses are U[0,1]. The phrase "the first KR0 ingredients"
  (p. 6) implies K·R0 = 220 distinct founder ingredients. But the stated pool at t0 is M·R0 = 60 *(ours)*, which is
  fewer than 220. **This is the main contradiction.**
- **A2. Initial pool.** Is the initial pool exactly M·R0, and are the founder ingredients members of it?
- **A3. Meaning of T.** T is called both "generations (iterations or 'time')" and "the number of recipes R = T". With
  t0 = R0 and R(t) = t, halting at R = T means T − R0 = 1180 copy–mutate steps for Fig. 3. The alternative is T
  iterations, giving T + R0 = 1220 recipes.
- **A4. Choosing loci.** Are the L loci chosen with or without replacement? "L(≠ K) … loci … to be mutated" suggests
  distinct loci, while "repeated L times" suggests independent draws.
- **A5. Pool draws.** Is j drawn uniformly from the whole pool (including never-used ingredients and ingredients
  already in the recipe)? This is implied but not explicit.
- **A6. Duplicates.** If j is already in the daughter, may it replace i (creating a duplicate and an effective size
  below K)? Not stated.
- **A7. Fitness of new pool ingredients.** That they are drawn from U[0,1] is implied by "ascribes to each ingredient i
  a random fitness" but is not restated for new ingredients.
- **A8. Pool growth within a step.** Does growth happen before or after the mutation? Is it exactly M new ingredients
  per step, and how is a non-integer M rounded? The text says only "at each time step … to maintain the ratio M
  fixed".
- **A9. Mother selection.** "randomly chose a recipe" presumably means uniform over all recipes, including the
  initial ones and all earlier daughters.
- **A10. Sequential mutations.** Within one daughter, the L comparisons act on the progressively mutated copy
  ("Within this copy"). This is assumed sequential, but not stated.
- **A11. Fixed recipe size.** Every recipe has exactly K ingredients, so the model cannot reproduce P^R(j) (Fig. 2
  inset), and the paper does not claim it does.
- **A12. Rank–frequency output.** Is f(r) for the model computed over all T recipes (including the R0 founders) and
  normalised by T?

**Outputs and fits**

- **A13. Averaging five runs (Fig. 3).** Rank-wise averaging of f(r) is assumed. Runs differ in how many ingredients
  were ever used, and the treatment of ranks missing from some runs is not stated.
- **A14. Eq. (1) fit.** The method (least squares on log f? weights?), the r-range, and whether C, a and r_c are shared
  by "all curves" or belong to one curve are not stated. It is also not stated which parameters draw the Fig. 3 solid
  curve.
- **A15. α fit.** Which cookery book(s) Fig. 2 shows is not stated (the triangles match Larousse in Fig. 1 *(ours)*),
  nor the "two-decade" fit range, the method, or whether α ≅ 1.73 holds for each book.
- **A16. Eq. (2) notation.** P_C(k) = 1 − Σ_k P^I(k) uses k as both the summation index and the argument, presumably
  Σ_{k'≤k}. The text says "used in more than k recipes".
- **A17. Fig. 4.** The model parameters, number of runs, γ fit range and fit method are not stated. The x-axis starts
  at t = 1, whereas the model starts at t0 = R0 (= 20 for Fig. 3). The curve peaks near t ≈ 20–25 *(ours)*. The
  y-axis has no readable tick labels other than "1", so magnitudes cannot be read.
- **A18. Fig. 5.** Parameters and number of runs are not stated. It is also not stated whether never-used pool
  ingredients are excluded; ranks shown run to about 1100, versus a final pool of M·T = 3600 *(ours)*.
- **A19. Contextual fitness.** The contextual f_i^I is "could be used", and nothing indicates it was used. We assume
  all results use plain f_i.
- **A20. Other books.** "Parameter fitting also gives a good agreement … for all the other cookery books", but no
  parameter values are reported for them.
- **A21. The no-fitness ablation (p. 6).** What "without fitness selection" means is not stated (always replace? never
  replace? replace with probability ½?).
- **A22. Randomness.** No RNG, seeds, or run-to-run variability is reported; there are no error bars anywhere.

**Data and editorial**

- **A23. Empirical databases.** Ingredient normalisation, the inclusion rules, and how the 40% Larousse sample was
  drawn are not described. The data are not released.
- **A24. Year mismatch.** The New Penguin Cookery Book is "(2001)" in Table 1 but 2004 in ref. [19].
- **A25. Fig. 1(a) markers.** The caption describes markers as Pleyn Delit circles, Dona Benta squares, New Penguin
  stars and Larousse triangles. The figure legend shows DB1969 as diamonds (the other markers match). Fig. 3's
  caption spells "Laurousse".
- **A26. Fig. 2 inset.** It is labelled P^R(j) but plotted as counts (y-axis up to 100).
- **A27. Exponent mismatch.** "α = 1 + 1/β" gives 1.763 *(ours)* against the reported α ≅ 1.73; the paper calls these
  "compatible" without a tolerance.

## 7. Reproduction card (bounded; no claim until a human freezes §7.3)

### 7.1 What to simulate

- **Primary run.** (T, K, L, M, R0) = (1200, 11, 4, 3, 20), U[0,1] fitness, **5 independent seeds**, as in Fig. 3.
  Pre-register one choice for each [GUESS] in §5.3 before running:
  - **IC-a.** Pool of M·R0 = 60 ingredients; each initial recipe has K ingredients drawn without replacement from it.
  - **IC-b.** K·R0 = 220 distinct founder ingredients form the initial pool; the pool then grows to M·R(t) once
    M·R(t) > 220.
  - Run both; designate IC-a as primary and report IC-b as sensitivity (A1/A2). Also run A3 both ways (1180 vs 1200
    steps).
- **Ablation.** The same setup without fitness selection. Pre-register the variant "always accept j" (A21).
- **No empirical reproduction.** The cookbook databases are not available (§3), so Fig. 1 and Fig. 2 cannot be
  recomputed. Targets are the paper's reported curve and exponents only.

### 7.2 Outputs to compare

| ID | Output | Paper's reference value | Location |
|---|---|---|---|
| O1 | 5-seed mean f(r) (fraction of the T recipes containing the rank-r ingredient) | eq. (1) with C = 8.7, a = 6.4, β = 1.31, r_c = 800 | p. 2–3, Fig. 3 |
| O2 | 1 − F_Total(t) vs t: shape (rise, then decay) and decay exponent γ | γ = 0.1 | p. 6, Fig. 4 |
| O3 | ingredient fitness vs rank (single seed): mean fitness; low-fitness founders at small r; high-fitness ingredients at large r | qualitative | p. 6–7, Fig. 5 |
| O4 | ablation: share of ranks r ≤ K·R0 held by founder ingredients, with vs without selection | qualitative ("over represented") | p. 6 |
| O5 | invariants: R = T; σ(t) = (t+1)/t; \|pool\| = M·R(t); every recipe has K slots | exact by construction | p. 4–6 |
| O6 | (descriptive only) ingredient-degree CCDF slope of the model | the paper reports α ≅ 1.73 for *data* only and does not report it for the model | p. 3 |

### 7.3 Tolerances and proposed acceptance criteria

**The paper states no tolerances.** It reports no error bars, goodness-of-fit statistics or fit ranges. Its wording
is "fits very well", "good agreement", "reasonably well", "≅". The criteria below are **project proposals**: they are
deliberately no stricter than visual agreement in the paper's own figures. A human must freeze them before the first
full run, and a failure is reported as such rather than tuned away.

- **AC-1 (O1, Fig. 3).**
  - PASS if |log10 f_sim(r) − log10 f_eq1(r)| ≤ 0.2 decade for at least 90% of ranks r ∈ [1, 500].
  - The tail (r > 500) is excluded because in Fig. 3 the paper's own model and fit visibly separate there *(ours,
    figure reading)*.
  - The 0.2-decade band is roughly the marker scatter between data and model in Fig. 3 *(ours)*.
- **AC-2 (O2, Fig. 4).**
  - PASS if 1 − F_Total(t) first rises and then decays, and an OLS fit of log(1 − F_Total) on log t over the decaying
    segment (argmax to the end) gives γ_sim ∈ [0.05, 0.2].
  - This is a factor of 2 around the reported 0.1, which has no stated uncertainty.
- **AC-3 (O3, Fig. 5).** All three must hold in at least 4 of 5 seeds:
  - (a) the mean fitness of ranked ingredients is > 0.5;
  - (b) at least one ingredient with f < 0.2 is among ranks r ≤ K·R0 and is a founder ingredient;
  - (c) at least one ingredient with f > 0.8 is at rank r > 500.
  - Thresholds are ours. The paper is qualitative.
- **AC-4 (O4).** PASS if the founder share of ranks 1…K·R0 is higher without selection than with it (mean over 5
  seeds).
- **AC-5 (O5).** These invariants must hold exactly; any violation is a bug, not a result.
- **Overall claim.** "Reproduced (bounded)" only if AC-1, AC-2 and AC-5 pass under the primary IC. AC-3 and AC-4 are
  supporting. All sensitivity variants are reported regardless of outcome. A founder-effect *statistic* is
  project-defined (the paper has none), so it is descriptive and must not be presented as reproducing a paper number.
- **Cross-check caution.** B15 reports α = 1.63 by CSN discrete MLE on the A1 corpus (DEC-024). The paper's
  α ≅ 1.73 comes from a line fit to the CCDF over an unstated "two-decade" range. The two numbers are **not
  comparable** unless the same estimator and range are used.

## 8. Related sources (not downloaded, not summarised)

- **Kinouchi et al., arXiv version.** arXiv:0802.4393v1 [physics.soc-ph], "The Nonequilibrium Nature of Culinary
  Evolution", submitted 29 Feb 2008.
  - arXiv comments: "15 pages, 5 figures, 1 table, submitted to Physical Review E". The journal-ref field points to
    NJP 10 073020.
  - Licence: arXiv perpetual non-exclusive distribution licence, http://arxiv.org/licenses/nonexclusive-distrib/1.0/.
  - URL: https://arxiv.org/abs/0802.4393.
  - This is a **pre-review** version and the published NJP version above governs. Because it is about twice as long,
    it *may* resolve A1–A8; it is worth fetching as SNAP-L13E-0002 if the owner agrees.
- **Jain A and Bagler G 2018 "Culinary evolution models for Indian cuisines".** *Physica A* **503** 170–176, DOI
  10.1016/j.physa.2018.02.176. Title, authors, volume, pages and Aug 2018 issue are verified via Crossref.
  - Crossref lists Elsevier TDM/user licences only, so the publisher version is not open access.
  - Freely accessible version: arXiv:1505.00155v1 [physics.soc-ph], submitted 1 May 2015. Comments "7 pages, 6
    figures, 3 tables". The licence is the arXiv non-exclusive distribution licence
    (http://arxiv.org/licenses/nonexclusive-distrib/1.0/). URL: https://arxiv.org/abs/1505.00155.
  - The 2015 preprint predates the 2018 journal version, and how closely the two match is **unverified**. Its method
    is deliberately not summarised here (SSOT §261.18 item 2 requires the original).

## 9. Human spot-check list (tick each against the PDF)

- [ ] Citation fields in §1 against PDF p. 1 (PDF page 2)
- [ ] Table 1, all 18 numbers and the footnote (p. 2 / PDF page 3)
- [ ] Eq. (1) form and β ≅ 1.31, C = 8.7, a = 6.4, r_c = 800 (p. 2–3 / PDF pages 3–4)
- [ ] α ≅ 1.73, eq. (2), and k^−0.73 in the Fig. 2 caption (p. 3–4 / PDF pages 4–5)
- [ ] Five-parameter definition and the update rule quotes (p. 4–5 / PDF pages 5–6)
- [ ] T = 1200, K = 11, L = 4, M = 3, R0 = 20; ⟨K⟩_Larousse = 10.8; "average of five runs" (p. 5 / PDF page 6)
- [ ] F^(k) and F_Total formulas (p. 5 / PDF page 6)
- [ ] γ = 0.1 and σ ≅ 1 (p. 6 / PDF page 7)
- [ ] Founder-effect and KR0 ablation quotes (p. 6 / PDF page 7); Fig. 5 caption (p. 7 / PDF page 8)
- [ ] Licence statement: confirm on the live iopscience page in a browser whether a CC licence is now shown (§2)

---

## 10. Preprint (arXiv:0802.4393v1) — what it resolves

*(Requested as "§7"; numbered §10 because §7–§9 already exist. Appended 2026-10-08.)*

### 10.0 Source and conventions

| Field | Value |
|---|---|
| Snapshot | `SNAP-L13E-0002` / `SRC-L13E-KINOUCHI2008-ARXIV` (`ledgers/snapshots/l13e_snapshots.jsonl`, line 2) |
| Local file | `data/raw/l13e/kinouchi2008_arxiv_v1.pdf` |
| sha256 | `885e618f6534c949135a3bf5a860548a5e138e15b471d9e4b1279c9afc8629d2` (re-hashed locally; matches ledger) |
| Size | 330,660 bytes, 15 pp |
| Version | Authors' pre-review version, arXiv v1 of 29 Feb 2008 |
| Licence | arXiv non-exclusive distribution licence |
| Approval | DEC-035 |
| Handling | Local only, no redistribution (applies to both PDFs) |

**Status of the earlier statements.** The statements in §2 ("arXiv … was **not** downloaded") and §8 ("not
downloaded") are **superseded** by SNAP-L13E-0002. Likewise, the approval note at the top is superseded by DEC-035.
Sections 2, 8 and the top note are left unedited per instruction.

**Page convention.** "pp. N" = the printed page number at the bottom of the preprint page, which equals the PDF page
here. "p. N" alone still means the **published** version (§1–§9 convention).

**Precedence.** The **published version (SNAP-L13E-0001) governs**; the preprint is supporting evidence only.

**Scope of reading.** The preprint was read in full: text via `pdftotext`, and every figure and the equations from the
rendered pages. The model description (pp. 5–6) is word-for-word the published text except for tense ("choose/copy"
vs "chose/copied") and minor punctuation. **No new algorithmic step or parameter value appears in the preprint.**

### 10.1 Status of each ambiguity

Totals: **RESOLVED 0 · PARTLY 1 · NOT ADDRESSED 23 · CONFLICTS-WITH-PUBLISHED 3**.

| A | Status | Evidence (preprint verbatim, pp.) |
|---|---|---|
| A1 initial recipes / founder pool | **PARTLY** | See note A1 below the table. |
| A2 initial pool | NOT ADDRESSED | Identical sentence: "Hence, starting with t0 = R0, at each time step there are R(t) = t recipes and MR(t) ingredients available to be used." (pp. 5) |
| A3 meaning of T | NOT ADDRESSED | Identical: "the number T of generations (iterations or "time") until the process is halted" (pp. 5); "the number of recipes is R = T = 1200 = R_Larousse" (pp. 6) |
| A4 loci with/without replacement | NOT ADDRESSED | Identical: "This process is repeated L times" (pp. 5) |
| A5 pool draw | NOT ADDRESSED | Identical: "an ingredient also randomly chosen from the ingredients pool" (pp. 5) |
| A6 duplicates in recipe | NOT ADDRESSED | No text on duplicates |
| A7 fitness of new ingredients | NOT ADDRESSED | Identical: "ascribes to each ingredient i a random fitness fi with values uniformly distributed in the interval [0,1]" (pp. 5) |
| A8 order and size of pool growth | NOT ADDRESSED | Identical: "Finally, at each time step, new ingredients are introduced in the ingredients pool to maintain the ratio M fixed." (pp. 5). "Finally" (in both versions) suggests growth after the daughter is added; it is not explicit. |
| A9 mother selection | NOT ADDRESSED | "we randomly choose a recipe (a "mother") and copy it" (pp. 5) |
| A10 sequential mutations | NOT ADDRESSED | Identical: "Within this copy we randomly choose an ingredient" (pp. 5) |
| A11 fixed recipe size K | NOT ADDRESSED | Same definition of K (pp. 5) |
| A12 model f(r) normalisation | NOT ADDRESSED | No model-side definition. The preprint's *empirical* counting wording differs from the published version (see N1). |
| A13 averaging five runs | NOT ADDRESSED | Identical caption: "by the model (circles, average of five runs)" (pp. 12) |
| A14 eq. (1) fit | **CONFLICTS-WITH-PUBLISHED** | See note A14 below the table. |
| A15 α fit (book, range, method, value) | **CONFLICTS-WITH-PUBLISHED** | See note A15 below the table. |
| A16 eq. (2) notation | NOT ADDRESSED | Identical: "PC(k) = 1 − Σ_k P^I(k), (2)" (pp. 4) |
| A17 Fig. 4 parameters / runs / axis / fit range | NOT ADDRESSED | Same figure: no y tick labels except "1", x from t = 1, peak near t ≈ 20 *(ours)*. Parameters and runs are not stated. Caption sign differs (see D6). |
| A18 Fig. 5 parameters / runs / unused ingredients | NOT ADDRESSED | Same figure and caption (pp. 14) |
| A19 contextual fitness used? | NOT ADDRESSED | Identical: "A more general fitness function could be used" (pp. 6) |
| A20 parameters for other books | NOT ADDRESSED | Identical: "Parameter fitting also gives a good agreement with the curves and values for all the other cookbooks considered." (pp. 6) |
| A21 meaning of "without fitness selection" | NOT ADDRESSED | "We tested an algorithm without fitness selection and observed that the conservation of the first KR0 ingredients (the founder effect) is so strong that they remain over represented in the population." (pp. 7–8). The ablation is still undefined; the preprint only adds the label "(the founder effect)". |
| A22 RNG / seeds / error bars | NOT ADDRESSED | None reported |
| A23 empirical preprocessing / Larousse sampling | NOT ADDRESSED | Identical corpus paragraph: "… contains a random sample (40%) of the whole population of recipes" (pp. 3). The counting-wording conflict is listed separately as N1. |
| A24 New Penguin year | NOT ADDRESSED | Same mismatch: Table 1 "New Penguin Cookery Book (2001)" (pp. 15) vs ref. 13 "J. Norman, The New Penguin Cookery Book. (Penguin, London, 2004)." (pp. 9) |
| A25 Fig. 1(a) markers | NOT ADDRESSED | Same mismatch: caption "Dona Benta 1969 (squares)" (pp. 10), while the legend shows DB1969 as diamonds *(ours)*. Fig. 3 caption also has "Laurousse" (pp. 12). |
| A26 Fig. 2 inset counts | NOT ADDRESSED | Same inset: y-axis 0–100, labelled P^R(j) (pp. 11) |
| A27 α = 1 + 1/β mismatch | **CONFLICTS-WITH-PUBLISHED** | See note A27 below the table. |

**Note A1 — initial recipes and the founder pool (PARTLY).**

- Preprint: "in spite of their low fitness some of the KR0 ingredients present in the initial R0 recipes have a
  strong difficulty of being probabilistically replaced." (pp. 7)
- What this settles: the founders are explicitly "the KR0 ingredients present in the initial R0 recipes", i.e. the
  initial recipes contain K ingredients each.
- What it does not say: how they are drawn, whether they are distinct, or their fitness law.
- The pool sentence is unchanged (pp. 5, see A2), so the K·R0 = 220 vs M·R0 = 60 contradiction **remains**.

**Note A14 — eq. (1) (CONFLICTS).**

- Preprint form (pp. 3, read from the rendered page): **f(r) = C / (a + r^β) · exp(−r/r_c)**.
- Preprint value: "The best fit exponent β ≅ 1.4 worked reasonably well for all curves" (pp. 4). No C, a or r_c is
  given.
- Published (p. 2–3): **f(r) = C/(a + r)^β · exp(−r/r_c)**, "β ≅ 1.31 … (the other parameters are C = 8.7, a = 6.4
  and r_c = 800)".
- Fit method and range are stated in neither version.

**Note A15 — α (CONFLICTS).**

- Preprint: "well fitted by P^I(k) ∝ k^−α with α ≅ 1.72" (pp. 4). Fig. 2 caption: "power law fitting k^−0.72 …
  Inset: Degree distribution P^R(j) for recipes." (pp. 11)
- Published: "α ≅ 1.73" (p. 3); "power law fitting k^−0.73 … for French recipes" (p. 4).
- The main-panel book, the fit range and the fit method are stated in neither version.

**Note A27 — the α = 1 + 1/β relation (CONFLICTS).**

- The preprint's numbers (β ≅ 1.4 (pp. 4), α ≅ 1.72 (pp. 4)) satisfy the stated relation: 1 + 1/1.4 = 1.714
  *(ours)*, within 0.006 of 1.72.
- The published version changed β to 1.31 (and the form of eq. (1)) and α to 1.73, but kept the sentence "It is
  compatible with the relation α = 1 + 1/β". Its numbers now give 1.763 *(ours)*.
- So the "compatible" claim was made for the preprint's β ≅ 1.4 under the a + r^β form.

### 10.2 Model details or parameter values present in the preprint but not in the published version

- **P1. Founder count tied to the initial recipes.** "some of the KR0 ingredients present in the initial R0 recipes"
  (pp. 7). The published version says only "some low fitness ingredients present in the initial R0 recipes" (p. 6);
  it uses KR0 only in the ablation sentence.
- **P2. Probabilistic replacement.** "have a strong difficulty of being probabilistically replaced" (pp. 7). The
  published version has "have a strong difficulty of being replaced and can even propagate during culinary growth"
  (p. 6).
- **P3. The ablation labelled as the founder effect.** "the conservation of the first KR0 ingredients (the founder
  effect)" (pp. 7–8).
- **P4. Wording of the selection mechanism.** Preprint: "Darwinian selection by ingredient fitness is essential"
  (pp. 7). Published: "ingredient competition due to differential fitness is essential" (p. 6). Same meaning.
- **No parameter value differs or is added.** Both versions have (T, K, L, M, R0) = (1200, 11, 4, 3, 20),
  ⟨K⟩_Larousse = 10.8, "average of five runs", U[0,1] fitness, γ = 0.1 (in the text) and σ ≅ 1. The preprint has
  **no** C, a or r_c; those exist only in the published version.

### 10.3 Differences in reported numbers and definitions

| # | Item | Preprint (pp.) | Published (p.) |
|---|---|---|---|
| D1 | eq. (1) functional form | C/(a + r^β)·exp(−r/r_c) (pp. 3) | C/(a + r)^β·exp(−r/r_c) (p. 2) |
| D2 | β | "β ≅ 1.4" (pp. 4) | "β ≅ 1.31" (p. 3) |
| D3 | C, a, r_c | not given | 8.7, 6.4, 800 (p. 3) |
| D4 | α | "α ≅ 1.72" (pp. 4) | "α ≅ 1.73" (p. 3) |
| D5 | Fig. 2 fitted slope | "k^−0.72" (pp. 11) | "k^−0.73" (p. 4) |
| D6 | γ in Fig. 4 caption | "γ = − 0.1" (pp. 13); the preprint text says "with γ = 0.1" (pp. 6), so the preprint is internally inconsistent | "γ = 0.1" (p. 6, caption and text) |
| D7 | Fig. 2 inset caption | "for recipes" (pp. 11) | "for French recipes" (p. 4); both texts say the French cookbook |
| D8 | Table 1 | identical, all 18 values and the footnote (pp. 15) *(machine-compared; human to confirm)* | p. 2 |
| D9 | Figs 1, 3, 4, 5 | visually identical to the published plots *(ours)*; the Fig. 3 y-label renders as "t(r)" (pp. 12) | — |

**New issue N1 — counting definition (not one of A1–A27).**

- Preprint: "For each cookbook database, we counted the number of times each ingredient appeared in the recipes and
  ordered them according to descending frequency." (pp. 3)
- Published: "we counted the number of recipes in which each ingredient appears" (p. 2), and it adds "The ingredient
  usage frequency f(r) is the relative number of recipes that use the ingredient with rank r" and "this is not a
  Zipfian lexical law" (p. 3).
- The two definitions agree only if no ingredient is listed twice in one recipe. Use the published definition
  (recipe-presence counts).

**Other non-numerical differences** (for completeness, no effect on the model):

- Affiliation 3 is "Faculdade Bandeirantes, 14010-060 Ribeirão Preto, SP, Brazil" (pp. 1); the published version has
  Universidade Tecnológica Federal do Paraná, Curitiba.
- The preprint lists PACS numbers (pp. 1), has a closing summary paragraph (pp. 8), and has 20 references against the
  published version's 33.
- The fitness interpretation omits "versatility" (pp. 5).
- "filogenetic trees" (pp. 6).

### 10.4 Consequences for §7 (recorded here; §7 is not edited)

- **AC-1 target.** Keep the published form C/(a + r)^β with (8.7, 6.4, 1.31, 800).
  - The preprint form cannot be used as a target because it has no C, a or r_c.
  - Fig. 3 is visually identical in both versions, so which formula actually drew its solid curve is **unknown**.
  - The published values give f(1) = 0.631 and f(500) = 0.00133 *(ours)*. This is consistent with reading Fig. 3 (f(1)
    ≈ 0.6, curve ending near 1.3×10⁻³ at r ≈ 550) *(ours)*.
- **A1 is not settled.** Keep the IC-a / IC-b sensitivity pair. The preprint wording ("the KR0 ingredients present in
  the initial R0 recipes") slightly favours K·R0 founder slots, which IC-b models. The pool-size contradiction with
  M·R0 still stands, so IC-a vs IC-b remains a pre-registered choice.
- **A27 / B15 cross-check.** Do not cite "α = 1 + 1/β compatibility" as a paper result for the published β. It holds
  for the preprint's (β ≅ 1.4, α ≅ 1.72), not for the published (1.31, 1.73).
- **Spot-check additions for §9.**
  - [ ] Preprint eq. (1) form and β ≅ 1.4 (pp. 3–4).
  - [ ] α ≅ 1.72 and k^−0.72 (pp. 4, 11).
  - [ ] Fig. 4 caption "γ = − 0.1" (pp. 13).
  - [ ] P1 quote (pp. 7).
  - [ ] N1 counting sentence (pp. 3).
  - [ ] Table 1 identical (pp. 15).
