r"""
Build the P0 research-spawn DAG (master prompt Part AF item 7) and seed
registry/research_spawns.csv. Asserts every P0 question from Part P is placed
in exactly one node, so nothing is dropped silently.

    python tools/build_p0_dag.py <path/to/master_prompt.md>
"""
from __future__ import annotations
import csv
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Budgets: S <= 25 sources, 1 run · M <= 50 sources, <= 2 runs · L <= 80 sources, <= 3 runs.
# Every node also obeys the Part AC stop rules and the Part Y6 untrusted-content rule.
NODES = [
 # id, wave, RS ids, title, depends, role, source classes, serves, budget, status
 ("N0", 1, ["RS-00-02"], "Experiment tracking + data versioning for a 2-person repo", [],
  "Data Engineer", "official docs; practitioner", "B00 (all DELs)", "S", "QUEUED"),
 ("N1", 1, ["RS-02-10"], "Scraping legality, copyright of recipe text, what may be stored vs derived", [],
  "Dataset/API Scout + Adversarial Reviewer", "official ToS/robots; legal/official; practitioner",
  "H2 decisions; A1-corpus reuse (Q5); DEL-3 input", "M", "QUEUED"),
 ("N2", 1, ["RS-02-01"], "CoSyLab/Foodoscope APIs and datasets that exist now", [],
  "Dataset/API Scout", "official pages; primary papers; CoSyLab GitHub",
  "email scope; DEL-1/3/4/5", "M", "QUEUED"),
 ("N3", 1, ["RS-02-07", "RS-06-06"], "Retention/processing-effect sources: USDA R6, Phenol-Explorer 3.0, EuroFIR — formats, coverage, licence", [],
  "Dataset/API Scout + Food-Chemistry Researcher", "official DB pages; primary papers",
  "DEL-1 (>=1,000 rows) — CRITICAL PATH", "M", "QUEUED"),
 ("N4", 1, ["RS-13-09"], "LLM literature-extraction accuracy in food science", [],
  "Primary-Literature Researcher", "primary scholarly", "DEL-1 (>=40 verified rows), G15-H", "S", "QUEUED"),
 ("N5", 1, ["RS-12-08"], "Small-data tabular baselines (LightGBM, TabPFN): evidence they win", [],
  "Statistician/Experiment Designer", "primary scholarly; code/data", "DEL-2 baselines", "S", "QUEUED"),
 ("N6", 1, ["RS-11-01"], "Recipe flow-graph representations and parsers (r-FG, action graphs)", [],
  "NLP/NER Benchmark Researcher", "primary scholarly; code/data", "DEL-3 state-graph schema", "M", "QUEUED"),
 ("N7", 1, ["RS-08-11", "RS-05-12"], "Instruction action/quantity/temperature/time extraction: SOTA, grammar vs learned", [],
  "NLP/NER Benchmark Researcher", "primary scholarly; code/data",
  "DEL-3 upstream (A1 events have null actions/duration/temperature)", "M", "QUEUED"),
 ("N8", 1, ["RS-17-06"], "Prior CoSyLab student work to avoid duplicating", [],
  "Primary-Literature Researcher + Dataset/API Scout", "official lab pages; CoSyLab GitHub; papers",
  "non-overlap promise in proposal §4", "S", "QUEUED"),

 ("N9", 2, ["RS-02-02"], "RecipeDB/RecipeDB2 field audit (step text, process/utensil labels, durations, temperatures)", ["N2"],
  "Dataset/API Scout", "official pages; API docs; papers", "§42 audit; DEL-3/5", "S", "QUEUED"),
 ("N10", 2, ["RS-06-01", "RS-06-02"], "Mechanism families and their temperature windows in real foods", ["N3"],
  "Food-Chemistry/Kinetics Researcher", "primary scholarly; reviews", "DEL-1 literature rows; DEL-5 answers", "L", "QUEUED"),
 ("N11", 2, ["RS-06-03", "RS-06-17"], "pH effects; ingredient/mixture pH and why averaging fails", ["N3"],
  "Food-Chemistry/Kinetics Researcher", "primary scholarly; official DBs", "DEL-1 condition fields; law B7", "M", "QUEUED"),
 ("N12", 2, ["RS-06-05"], "Kinetic parameters (Ea, k, order) for vitamins, pigments, acrylamide, HMF, browning", ["N3"],
  "Food-Chemistry/Kinetics Researcher", "primary scholarly; reviews", "DEL-1 kinetics rows; M3 stretch", "M", "QUEUED"),
 ("N13", 2, ["RS-06-07"], "Raw-vs-cooked GC-MS volatile studies census + extraction schema", ["N3", "N4"],
  "Food-Chemistry Researcher + Evidence Verifier", "primary scholarly",
  "DEL-1 >=40 verified rows (first cells §144.3)", "L", "QUEUED"),
 ("N14", 2, ["RS-06-12", "RS-06-13"], "Frying degradation/acrylamide guidance; food-safety temperatures (authoritative only)", ["N1"],
  "Safety/Warning Curator", "official/standards only (USDA FSIS, FSSAI)", "DEL-5 safety constraints", "M", "QUEUED"),
 ("N15", 2, ["RS-05-01", "RS-05-02"], "Existing process ontologies and the process-family hierarchy", ["N2"],
  "Process Ontologist", "official ontologies; primary scholarly", "DEL-1 process normalisation; DEL-3 ops", "M", "QUEUED"),
 ("N16", 2, ["RS-04-08", "RS-09-01", "RS-09-02"], "Ingredient master lists, food entity linking, product-vs-modifier boundaries", ["N2"],
  "Dataset/API Scout + NLP Researcher", "official DBs/ontologies; primary scholarly",
  "DEL-1 'names normalised to RecipeDB/FlavorDB'", "M", "QUEUED"),
 ("N17", 2, ["RS-10-01", "RS-10-02", "RS-10-03", "RS-10-04", "RS-02-05"], "Units by locale, verbal quantities, count portions, densities; portion databases", ["N1"],
  "Metrology/Quantity Researcher", "official/standards; official DBs", "DEL-3 reserve/split amounts; DEL-1 units", "L", "QUEUED"),
 ("N18", 2, ["RS-EDA-01", "RS-EDA-02"], "EDA standards; principled rank-frequency fitting and pitfalls", [],
  "EDA Analyst", "primary scholarly; code/data", "DEL-1 data card + audit", "S", "QUEUED"),
 ("N19", 2, ["RS-07-05"], "Gold annotation protocols and agreement for recipe semantics", ["N6"],
  "Statistician + NLP Researcher", "primary scholarly", "DEL-3 40 gold recipes + 30 sessions", "S", "QUEUED"),
 ("N20", 2, ["RS-03-01", "RS-03-02"], "Ahn 2011 and Jain-Rakhi-Bagler 2015 exact methods and numbers", [],
  "Code/Repo Reproducer", "primary scholarly; code/data", "B03 first code (§128, §279.3)", "S", "QUEUED"),

 ("N21", 3, ["RS-02-03", "RS-02-04"], "Public recipe corpora and Indian/Hinglish sources with usable licences", ["N1"],
  "Dataset/API Scout", "official dataset pages; licences", "fallback DEL-3 input if Q5 rejects A1 reuse", "M", "CONDITIONAL-ON-Q5"),
 ("N22", 3, ["RS-00-01"], "Ray vs Slurm vs Kubernetes for the ~100-node cluster", [],
  "Data Engineer", "official docs; practitioner", "compute adapter", "S", "BLOCKED-ON-HUMAN (Q3)"),
 ("N23", 3, ["RS-00-03"], "Polite large-scale crawling stack", ["N1"],
  "Data Engineer", "official docs; practitioner", "only if new scraping is approved", "S", "DEFERRED (H2)"),
 ("N24", 3, ["RS-01-01"], "Turning a long spec into executable registries", [],
  "Research Architect", "practitioner; standards", "B01 (can proceed without it)", "S", "OPTIONAL"),
 ("N25", 3, ["RS-02-06", "RS-04-01", "RS-04-02"], "Molecule databases, ingredient-molecule mappings, molecule identity pitfalls", [],
  "Dataset/API Scout + Food-Chemistry Researcher", "official DBs; primary scholarly", "B04 / L12", "L", "DEFERRED (H8)"),
 ("N26", 3, ["RS-07-01", "RS-07-02", "RS-07-03", "RS-07-04"], "60k-100k Silver factory: sampling, near-dup, LLM annotation at scale, Silver QA", [],
  "Data Engineer + Statistician", "primary scholarly; practitioner", "B07", "L", "DEFERRED (H8)"),
 ("N27", 3, ["RS-08-01", "RS-08-02"], "NER SOTA protocols; RecipeDB3 notebook reproduction details", [],
  "Code/Repo Reproducer", "primary scholarly; code/data", "B08", "M", "DEFERRED (H8)"),
 ("N28", 3, ["RS-14-02"], "Operational definitions of the six similarity types", [],
  "Statistician + Research Architect", "primary scholarly", "B14 / FlavorTwin stretch", "M", "DEFERRED (H8)"),
]
HUMAN = [("RS-17-05", "Course deliverable expectations and grading", "Q2 to the humans/professor")]


def main(argv):
    mp = pathlib.Path(argv[1]).read_text(encoding="utf-8").split("\n")
    grp, p0 = None, {}
    for l in mp:
        m = re.match(r"^### (RS-[0-9A-Z]+) ", l)
        if m:
            grp = m.group(1)
            continue
        m = re.match(r"^(\d+)\.\s+\((P[012])\)\s+(.*)", l)
        if m and grp and m.group(2) == "P0":
            p0[f"{grp}-{int(m.group(1)):02d}"] = m.group(3)
    placed = [r for n in NODES for r in n[2]] + [h[0] for h in HUMAN]
    dup = {r for r in placed if placed.count(r) > 1}
    missing = set(p0) - set(placed)
    unknown = set(placed) - set(p0)
    assert not dup, f"placed twice: {dup}"
    assert not missing, f"P0 not placed: {sorted(missing)}"
    assert not unknown, f"not a P0 id: {sorted(unknown)}"
    ids = {n[0] for n in NODES}
    for n in NODES:
        assert set(n[4]) <= ids, f"{n[0]} depends on unknown node"

    reg = ROOT / "registry"
    reg.mkdir(exist_ok=True)
    with (reg / "research_spawns.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["rs_id", "priority", "node", "wave", "question", "depends_on",
                    "agent_role", "source_classes", "serves", "budget", "status",
                    "brief_path", "outcome"])
        for n in NODES:
            for r in n[2]:
                w.writerow([r, "P0", n[0], n[1], p0[r], " ".join(n[4]), n[5], n[6],
                            n[7], n[8], n[9], f"research/briefs/{r}.md", ""])
        for r, _, route in HUMAN:
            w.writerow([r, "P0", "-", 0, p0[r], "", "humans", "", route, "-",
                        "BLOCKED-ON-HUMAN", "", ""])
    waves = {1: [], 2: [], 3: []}
    for n in NODES:
        waves[n[1]].append(n)
    print(f"P0 questions in Part P: {len(p0)}; placed: {len(placed)} "
          f"({sum(len(n[2]) for n in NODES)} in {len(NODES)} nodes + {len(HUMAN)} human)")
    for k, v in waves.items():
        print(f"  wave {k}: {len(v)} nodes, {sum(len(n[2]) for n in v)} questions")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
