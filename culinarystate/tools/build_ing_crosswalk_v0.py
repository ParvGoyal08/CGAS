r"""
K6 + P12 — internal ING- registry v0, recipe-vocabulary crosswalk, and evidence-coverage audit.

    .venv/bin/python tools/build_ing_crosswalk_v0.py

Recipe vocabulary = the A1 course corpus (BBC Good Food, 11,934 recipes; used locally, only
aggregates reported). DEL-3 will use RecipeDB once access arrives; the same rules then apply.

Ordered regex rules, first match wins. Outcomes:
  MAPPED_CONCEPT     the recipe ingredient IS the ING concept            (e.g. egg → ING-egg)
  MAPPED_CATEGORY    member of a USDA R6 category ING                    (onion → ING-vegetable-other)
  DERIVED_PRODUCT    a product of the food, not the food                 (chicken stock, lemon juice, tomato purée)
  NO_R6_CLASS        a class R6 never measures — an evidence gap, not a mapping gap (herbs, spices, fats, sugars …)
  A1_ARTEFACT        a fragment produced by the A1 NER/canonicaliser ("chif", "frac", "red"), not an ingredient
  UNRESOLVED         no rule fired → P12 queue
All links are PROPOSED (rules written by Parv's session; human audit pending). Nothing is
inferred by an LLM.
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
from collections import Counter

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
A1 = ROOT.parents[1] / "A1/outputs/Q1/Q1c_recipe_ingredient.csv"
OUT = ROOT / "ledgers/ingredients"

W = lambda *xs: r"\b(" + "|".join(xs) + r")\b"  # noqa: E731
RULES = [
    # --- A1 extraction artefacts: fragments, not ingredients (exact-name match only)
    ("Z-A1-ARTEFACT", r"^(chif|frac|red|white|green|yellow|black|fast-action|sunflower|fresh|dried|ground|large|small|"
                      r"medium|plain|whole|light|dark|free-range|unwaxed|ripe|baby|mixed|frozen|cooked|raw|tinned)$",
     "A1_ARTEFACT", "fragment"),
    # --- derived products and seasonings that would otherwise hit a food rule
    ("X-PEPPER-BARE", r"^pepper$", "NO_R6_CLASS", "spice_ambiguous_bare_pepper"),
    ("X-VINEGAR", W("vinegar"), "NO_R6_CLASS", "condiment"),
    ("X-SPICE-PEPPER", W("black pepper", "white pepper", "peppercorns?", "cayenne( pepper)?", "pepper flakes", "chilli flakes",
                         "chilli powder", "chili powder", "pink peppercorns?", "szechuan pepper", "sichuan pepper"), "NO_R6_CLASS", "spice"),
    ("X-SOFT-DRINK", W("ginger beer", "ginger ale", "lemonade", "cola", "tonic water", "soda water", "sparkling water"),
     "NO_R6_CLASS", "beverage_non_alcoholic"),
    ("X-BAKED", W("bourbon biscuits?", "biscuits?", "cakes?", "sponge fingers", "savoiardi", "amaretti( biscuits)?"),
     "DERIVED_PRODUCT", "product"),
    ("X-CONFECTION", W("chocolate (mini )?eggs?", "easter eggs?", "creme eggs?", "glacé cherr(y|ies)", "mixed peel",
                       "candied peel", "crystallised ginger", "stem ginger"), "NO_R6_CLASS", "sweetener_or_confection"),
    ("X-MISO-SPICEBERRY", W("[a-z ]*miso", "allspice( berries)?", "juniper berries", "pink peppercorns?"), "NO_R6_CLASS",
     "spice_or_seasoning"),
    ("A-ALCOHOL", W("wine", "red wine", "white wine", "beer", "ale", "stout", "cider", "brandy", "cognac", "rum", "vodka", "gin",
                    "whisky", "whiskey", "sherry", "port", "marsala", "vermouth", "liqueur", "kirsch", "bourbon", "tequila",
                    "prosecco", "champagne", "calvados", "amaretto", "cointreau", "grand marnier"),
     "MAPPED_CATEGORY", "ING-alcoholic-beverage"),
    ("X-DERIVED", W("stock", "broth", "juice", "zest", "purée", "puree", "paste", "passata", "sauce", "ketchup", "extract",
                    "essence", "oil", "powder", "jam", "marmalade", "chutney", "pickle", "pickled", "cordial", "curd",
                    "stock cube", "gravy", "crisps?", "jelly", "concentrate", "syrup", "sugar", "milk chocolate",
                    "coconut milk", "almond milk", "oat milk", "soy milk", "buttermilk", "cornflour", "mayonnaise",
                    "pesto", "spread", "molasses", "almond butter", "cashew butter", "coconut cream", "coconut yog(h)?urt",
                    "coconut water", "creamed coconut", "houmous", "hummus", "tahini", "nut butter", "peanut butter", "breadcrumbs?", "bread",
                    "puff pastry", "shortcrust pastry", "filo pastry", "pastry", "digestive biscuits?", "biscuits?",
                    "salad", "green salad", "tortillas?", "wraps?", "pitta", "naan", "brioche", "croissants?", "sponge"),
     "DERIVED_PRODUCT", "product"),
    # --- compound names that a general rule below would capture wrongly (pre-emption)
    ("P-TOMATO-BEEF", W("beef tomato(es)?"), "MAPPED_CONCEPT", "ING-tomato"),
    ("P-LETTUCE-LAMB", W("lamb'?s? lettuce"), "MAPPED_CATEGORY", "ING-vegetable-greens"),
    ("P-NOODLES", W("egg noodles?", "rice noodles?", "noodles?", "rice paper"), "NO_R6_CLASS", "grain_not_in_r6"),
    ("P-HERB-CITRUS", W("lime leaves", "kaffir lime leaves", "lemon thyme", "lemon verbena", "orange blossom water",
                        "orange flower water"), "NO_R6_CLASS", "herb_or_seed_spice"),
    ("P-VEG-COMPOUND", W("green beans?", "broad beans?", "runner beans?", "fine beans?", "french beans?", "banana shallots?",
                         "[a-z-]+ mushrooms?", "mushrooms?", "egg plants?", "eggplants?", "water chestnuts?",
                         "(orange|yellow|red|green|cherry|romano|padron|piquillo|sweet) peppers?", "artichoke hearts?",
                         "celery hearts?"), "MAPPED_CATEGORY", "ING-vegetable-other"),
    ("P-GREENS-COMPOUND", W("(little )?gem lettuce hearts?", "lettuce hearts?"), "MAPPED_CATEGORY", "ING-vegetable-greens"),
    ("P-FLOUR-OF", W("(rice|potato|pasta|chickpea|coconut|almond|buckwheat|spelt|rye|gram) flour"), "MAPPED_CATEGORY",
     "ING-flour-meal"),
    ("P-FISH-STEAK", W("(tuna|salmon|swordfish|cod|halibut) steaks?"), "MAPPED_CATEGORY", "ING-finfish"),
    # --- concepts
    ("M-EGG", W("eggs?", "egg yolks?", "egg whites?", "duck eggs?", "quail eggs?"), "MAPPED_CONCEPT", "ING-egg"),
    ("M-SAUSAGE", W("sausages?", "chorizo", "frankfurters?", "hot dogs?", "salami", "pepperoni", "black pudding", "merguez"),
     "MAPPED_CATEGORY", "ING-sausage"),
    ("M-BACON", W("bacon", "pancetta", "lardons?", "streaky bacon", "back bacon"), "MAPPED_CONCEPT", "ING-bacon"),
    ("M-HAM", W("ham", "prosciutto", "parma ham", "serrano ham", "gammon"), "MAPPED_CONCEPT", "ING-ham"),
    ("M-LIVER", W("liver", "livers"), "MAPPED_CONCEPT", "ING-liver"),
    ("M-ORGAN", W("kidneys?(?! beans?)", "(ox|lamb'?s?|chicken|pig'?s?) hearts?", "tongue", "tripe", "sweetbreads?", "oxtail"), "MAPPED_CATEGORY", "ING-organ-meat-non-liver"),
    ("M-CHICKEN", W("chicken", "chicken breasts?", "chicken thighs?", "chicken legs?", "chicken wings?", "poussin"), "MAPPED_CONCEPT", "ING-chicken"),
    ("M-TURKEY", W("turkey"), "MAPPED_CONCEPT", "ING-turkey"),
    ("M-VEAL", W("veal"), "MAPPED_CONCEPT", "ING-veal"),
    ("M-LAMB", W("lamb", "mutton", "lamb mince", "lamb shoulder", "lamb leg"), "MAPPED_CONCEPT", "ING-lamb"),
    ("M-PORK", W("pork", "pork belly", "pork shoulder", "pork mince", "pork chops?", "pork loin", "pork fillet"), "MAPPED_CONCEPT", "ING-pork"),
    ("M-BEEF", W("beef", "steak", "sirloin", "rib-eye", "ribeye", "brisket", "beef mince", "fillet steak", "rump steak", "skirt steak",
                 "braising steak", "stewing beef", "short ribs?"), "MAPPED_CONCEPT", "ING-beef"),
    ("M-FINFISH", W("fish", "salmon", "cod", "haddock", "tuna", "mackerel", "trout", "sea bass", "bream", "hake", "pollock", "sardines?",
                    "anchov(y|ies)", "halibut", "monkfish", "plaice", "sole", "tilapia", "swordfish", "kipper", "basa", "coley",
                    "white fish", "smoked salmon", "smoked haddock", "red mullet", "snapper", "herring"), "MAPPED_CATEGORY", "ING-finfish"),
    ("M-SHELLFISH", W("prawns?", "king prawns?", "shrimps?", "crab", "crabmeat", "lobster", "mussels?", "clams?", "oysters?",
                      "scallops?", "squid", "langoustines?", "crayfish", "cockles?"), "MAPPED_CATEGORY", "ING-shellfish"),
    ("M-SWEETPOTATO", W("sweet potato(es)?"), "MAPPED_CONCEPT", "ING-sweet-potato"),
    ("M-POTATO", W("potato(es)?", "new potato(es)?", "baking potato(es)?", "floury potato(es)?", "waxy potato(es)?",
                   "maris piper", "king edward", "charlotte potato(es)?", "jersey royals?"), "MAPPED_CONCEPT", "ING-potato"),
    ("M-TOMATO", W("tomato(es)?", "cherry tomato(es)?", "plum tomato(es)?", "vine tomato(es)?", "chopped tomato(es)?",
                   "tinned tomato(es)?", "sun-dried tomato(es)?", "beef tomato(es)?"), "MAPPED_CONCEPT", "ING-tomato"),
    ("M-RICE", W("rice", "basmati( rice)?", "arborio( rice)?", "risotto rice", "jasmine rice", "brown rice", "long-grain rice",
                 "wild rice", "sushi rice", "paella rice"), "MAPPED_CONCEPT", "ING-rice"),
    ("M-PASTA", W("pasta", "spaghetti", "penne", "linguine", "tagliatelle", "fusilli", "macaroni", "lasagne( sheets)?", "orzo",
                  "rigatoni", "pappardelle", "farfalle", "conchiglie", "fettuccine", "orecchiette", "gnocchi", "ravioli",
                  "tortellini", "spaghettini", "bucatini", "cannelloni", "vermicelli"), "MAPPED_CATEGORY", "ING-pasta"),
    ("M-OATS", W("oats?", "porridge oats", "rolled oats", "jumbo oats", "oatmeal"), "MAPPED_CONCEPT", "ING-oatmeal"),
    ("M-FLOUR", W("flour", "plain flour", "self-raising flour", "strong white flour", "wholemeal flour", "bread flour",
                  "cornmeal", "polenta", "semolina", "spelt flour", "rye flour", "buckwheat flour", "gram flour", "00 flour"),
     "MAPPED_CATEGORY", "ING-flour-meal"),
    ("M-LEGUME", W("lentils?", "red lentils?", "puy lentils?", "green lentils?", "chickpeas?", "kidney beans?", "black beans?",
                   "cannellini beans?", "butter beans?", "borlotti beans?", "haricot beans?", "pinto beans?", "split peas?",
                   "dal", "dhal", "mung beans?", "flageolet beans?", "black-eyed beans?", "adzuki beans?", "baked beans",
                   "mixed beans", "white beans?", "beans"), "MAPPED_CATEGORY", "ING-legume"),
    ("M-NUT", W("almonds?", "ground almonds", "flaked almonds", "walnuts?", "cashews?", "cashew nuts?", "pecans?", "hazelnuts?",
                "pistachios?", "peanuts?", "macadamias?", "macadamia nuts?", "brazil nuts?", "pine nuts?", "nuts", "mixed nuts",
                "chestnuts?"), "MAPPED_CATEGORY", "ING-nut"),
    ("M-CHEESE", W("cheese", "cheddar", "parmesan", "mozzarella", "feta", "ricotta", "gruy[eè]re", "halloumi", "goat's cheese",
                   "mascarpone", "stilton", "brie", "camembert", "paneer", "pecorino", "emmental", "manchego", "gorgonzola",
                   "cream cheese", "soft cheese", "comté", "comte", "taleggio", "fontina", "red leicester", "wensleydale",
                   "blue cheese", "dolcelatte", "burrata", "cottage cheese", "quark", "grana padano", "vegetarian hard cheese"),
     "MAPPED_CATEGORY", "ING-cheese"),
    ("M-MILK", W("milk", "whole milk", "semi-skimmed milk", "skimmed milk", "full-fat milk", "evaporated milk",
                 "condensed milk"), "MAPPED_CONCEPT", "ING-milk"),
    ("M-CITRUS", W("lemons?", "limes?", "oranges?", "blood oranges?", "grapefruit", "clementines?", "satsumas?", "mandarins?",
                   "tangerines?", "kumquats?", "yuzu"), "MAPPED_CATEGORY", "ING-fruit-citrus"),
    ("M-DRIEDFRUIT", W("raisins?", "sultanas?", "currants?", "prunes?", "dried apricots?", "dried figs?", "dates?",
                       "medjool dates?", "dried cranberr(y|ies)", "dried cherr(y|ies)", "dried fruit", "mixed dried fruit"), "MAPPED_CATEGORY", "ING-fruit"),
    ("M-FRUIT", W("apples?", "bramley apples?", "eating apples?", "pears?", "bananas?", "mangoes?", "mango", "pineapple",
                  "peach(es)?", "nectarines?", "plums?", "apricots?", "cherr(y|ies)", "strawberr(y|ies)", "raspberr(y|ies)",
                  "blueberr(y|ies)", "blackberr(y|ies)", "grapes?", "figs?", "kiwi( fruit)?", "melon", "watermelon",
                  "pomegranate( seeds)?", "rhubarb", "cranberr(y|ies)", "passion fruit", "papaya", "lychees?", "gooseberr(y|ies)",
                  "redcurrants?", "blackcurrants?", "berries", "mixed berries", "quince", "coconut", "avocados?"),
     "MAPPED_CATEGORY", "ING-fruit-non-citrus"),
    ("M-GREENS", W("spinach", "baby spinach", "kale", "chard", "swiss chard", "cabbage", "red cabbage", "savoy cabbage",
                   "cavolo nero", "spring greens", "collard greens", "watercress", "rocket", "lettuce", "pak choi", "bok choy",
                   "greens", "chicory", "radicchio", "romaine", "little gem( lettuce)?", "salad leaves", "mixed salad leaves",
                   "sorrel", "endive"), "MAPPED_CATEGORY", "ING-vegetable-greens"),
    ("M-ROOTS", W("carrots?", "parsnips?", "turnips?", "swede", "beetroots?", "beets?", "celeriac", "radish(es)?",
                  "jerusalem artichokes?", "kohlrabi", "mooli", "daikon"), "MAPPED_CATEGORY", "ING-vegetable-roots"),
    # --- herbs/spices before vegetables ("coriander", "chilli" are ambiguous: leaf/seed/fresh/dried)
    ("N-HERB", W("herb", "coriander", "parsley", "flat-leaf parsley", "thyme", "basil", "mint", "bay( leaf| leaves)?", "bay leaves",
                 "rosemary", "sage", "dill", "oregano", "tarragon", "chives?", "chervil", "marjoram", "lemongrass",
                 "kaffir lime leaves", "lime leaves", "curry leaves", "fresh herbs", "mixed herbs", "herbs", "lovage",
                 "fennel seeds?", "coriander seeds?", "cumin seeds?", "mustard seeds?", "nigella seeds?", "caraway seeds?",
                 "celery seeds?", "fenugreek( seeds)?"), "NO_R6_CLASS", "herb_or_seed_spice"),
    ("N-SPICE", W("anise", "salt", "sea salt", "cumin", "ground cumin", "cinnamon", "nutmeg", "paprika", "smoked paprika", "turmeric",
                  "garam masala", "cardamom( pods)?", "cloves", "allspice", "star anise", "saffron", "sumac", "za'atar",
                  "ras el hanout", "five-spice", "chinese five-spice", "curry powder", "mixed spice", "ground ginger",
                  "ground coriander", "chipotle", "harissa", "sea salt flakes", "mustard", "dijon mustard",
                  "wholegrain mustard", "english mustard", "vanilla( pod| bean)?", "vanilla pods?", "spices?"),
     "NO_R6_CLASS", "spice_or_seasoning"),
    ("N-GRAIN", W("couscous", "quinoa", "bulgur( wheat)?", "freekeh", "pearl barley", "barley", "buckwheat", "millet",
                  "noodles?", "rice noodles?", "egg noodles?", "udon", "soba"), "NO_R6_CLASS", "grain_not_in_r6"),
    ("N-GENERIC", r"^(vegetables?|fruits?|meat|fish fillets?)$", "NO_R6_CLASS", "generic_term_needs_context"),
    ("N-FAT", W("butter", "unsalted butter", "salted butter", "ghee", "lard", "dripping", "suet", "margarine", "goose fat",
                "duck fat", "vegetable shortening"), "NO_R6_CLASS", "fat"),
    ("N-DAIRY-CREAM", W("cream", "double cream", "single cream", "whipping cream", "soured cream", "sour cream", "crème fraîche",
                        "creme fraiche", "clotted cream", "yogurt", "yoghurt", "greek yogurt", "natural yogurt", "fromage frais",
                        "kefir"), "NO_R6_CLASS", "cream_or_cultured_dairy"),
    ("N-SWEET", W("honey", "maple", "golden syrup", "treacle", "black treacle", "molasses", "agave", "chocolate", "dark chocolate",
                  "white chocolate", "cocoa", "cocoa powder", "caster sugar", "icing sugar", "brown sugar", "muscovado",
                  "demerara", "marzipan", "fondant", "sprinkles"), "NO_R6_CLASS", "sweetener_or_confection"),
    ("N-LEAVEN", W("baking powder", "bicarbonate of soda", "yeast", "fast-action dried yeast", "dried yeast", "gelatine",
                   "cream of tartar", "agar"), "NO_R6_CLASS", "leavening_or_setting_agent"),
    ("N-CONDIMENT", W("soy sauce", "fish sauce", "worcestershire sauce", "miso", "tamari", "capers", "olives", "kalamata olives",
                      "green olives", "black olives", "mirin", "gochujang", "tofu", "tempeh", "water", "ice", "seeds", "sesame seeds",
                      "sunflower seeds", "pumpkin seeds", "chia seeds", "linseeds?", "flaxseeds?", "poppy seeds", "seed", "olive"),
     "NO_R6_CLASS", "condiment_or_other"),
    ("M-VEG-OTHER", W("onions?", "red onions?", "white onions?", "brown onions?", "spring onions?", "shallots?", "banana shallots?",
                      "leeks?", "garlic", "garlic cloves?", "peppers?", "red peppers?", "yellow peppers?", "green peppers?",
                      "romano peppers?", "courgettes?", "aubergines?", "mushrooms?", "chestnut mushrooms?", "button mushrooms?",
                      "portobello mushrooms?", "shiitake( mushrooms)?", "wild mushrooms?", "porcini", "broccoli",
                      "tenderstem broccoli", "purple sprouting broccoli", "cauliflower", "celery", "celery sticks?", "cucumbers?",
                      "peas", "frozen peas", "petits pois", "mangetout", "sugar snap peas", "green beans?", "fine beans?",
                      "runner beans?", "broad beans?", "edamame( beans)?", "asparagus", "sweetcorn", "corn", "corn on the cob",
                      "baby corn", "fennel", "fennel bulbs?", "okra", "squash", "butternut squash", "pumpkin", "artichokes?",
                      "brussels sprouts?", "chillies", "chilli", "red chillies?", "green chillies?", "red chilli", "green chilli",
                      "bird's-eye chillies?", "scotch bonnet( chilli)?", "red chilly", "green chilly", "chilly", "pea",
                      "beansprout", "jalapeños?", "jalapenos?", "ginger", "fresh ginger",
                      "beansprouts", "bean sprouts", "water chestnuts", "bamboo shoots", "samphire", "marrow", "courgette flowers",
                      "spring onion"), "MAPPED_CATEGORY", "ING-vegetable-other"),
]
COMPILED = [(rid, re.compile(pat, re.I), outcome, target) for rid, pat, outcome, target in RULES]


def classify(name: str):
    for rid, rx, outcome, target in COMPILED:
        if rx.search(name):
            return rid, outcome, target
    return "", "UNRESOLVED", ""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ev = pd.read_parquet(ROOT / "ledgers/evidence/evidence_v0.parquet")
    reg = ev.groupby("ingredient_id").agg(granularity=("ingredient_granularity", "first"),
                                          food_group=("food_group", "first"),
                                          r6_examples=("ingredient_raw", lambda s: "; ".join(sorted(set(s))[:3])),
                                          evidence_rows=("evidence_id", "size")).reset_index()
    reg.to_csv(OUT / "ing_v0.csv", index=False)
    known = set(reg["ingredient_id"])
    freq = Counter()
    with A1.open(encoding="utf-8") as fh:
        r = csv.reader(fh)
        next(r)
        for _, ing in r:
            freq[ing] += 1
    rows = []
    for name, n in freq.most_common():
        rid, outcome, target = classify(name)
        if outcome.startswith("MAPPED") and target not in known:
            raise SystemExit(f"rule {rid} targets unknown {target}")
        rows.append({"alias": name, "mentions": n, "rule_id": rid, "outcome": outcome,
                     "ingredient_id": target if outcome.startswith("MAPPED") else "",
                     "class": target if not outcome.startswith("MAPPED") else "", "status": "PROPOSED"})
    al = pd.DataFrame(rows)
    al.to_csv(OUT / "alias_a1_v0.csv", index=False)
    tot = al["mentions"].sum()
    by_outcome = al.groupby("outcome")["mentions"].sum().sort_values(ascending=False)
    rep = {
        "corpus": "A1 (BBC Good Food, 11,934 recipes; local only)", "distinct_names": len(al), "mentions": int(tot),
        "mention_share_by_outcome": {k: round(v / tot, 4) for k, v in by_outcome.items()},
        "name_share_by_outcome": al["outcome"].value_counts(normalize=True).round(4).to_dict(),
        "mapped_mentions_by_ing": al[al["ingredient_id"] != ""].groupby("ingredient_id")["mentions"].sum()
                                  .sort_values(ascending=False).to_dict(),
        "no_r6_class_mentions": al[al["outcome"] == "NO_R6_CLASS"].groupby("class")["mentions"].sum()
                                .sort_values(ascending=False).to_dict(),
        "unresolved_top50": al[al["outcome"] == "UNRESOLVED"].head(50)[["alias", "mentions"]].values.tolist(),
        "rules": len(RULES), "status": "all links PROPOSED — human audit pending (sample ≥ 200 aliases, stratified by rule)",
    }
    al[al["outcome"] == "UNRESOLVED"].head(300).to_csv(OUT / "unresolved_queue_a1_v0.csv", index=False)
    (OUT / "crosswalk_a1_v0.report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False))
    print(json.dumps({k: rep[k] for k in ("mention_share_by_outcome", "name_share_by_outcome")}, indent=1))
    print("top unresolved:", rep["unresolved_top50"][:25])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
