r"""
T19 / SSOT P12 — tool / utensil ledger TOOL- v0.

    .venv/bin/python tools/build_tool_v0.py

Sources (local, already in the project): proc_v0 `encodes_tool` (the process names its tool),
RecipeDB process-vocabulary terms classed TOOL (Bagler 2022 Table S2, cited vocabulary), and the
decision layer's definitional requirements (bake/roast → oven …).
Identity + process compatibility ONLY. material / geometry / capacity / heat-source compatibility /
physical implications / safety warnings are UNKNOWN until an authoritative source is attached —
nothing physical or safety-related is asserted here.
"""
from __future__ import annotations

import csv
import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "ledgers/tools/tool_v0.csv"
KIND = {  # PROPOSED coarse kind; reviewer: Kush
    "oven": "APPLIANCE", "microwave oven": "APPLIANCE", "air fryer": "APPLIANCE", "pressure cooker": "APPLIANCE",
    "refrigerator": "APPLIANCE", "freezer": "APPLIANCE", "slow cooker": "APPLIANCE", "hob": "HEAT_SOURCE",
    "barbecue": "HEAT_SOURCE", "grill": "HEAT_SOURCE", "griddle": "COOKWARE", "pan": "COOKWARE", "wok": "COOKWARE",
    "pot": "COOKWARE", "pot with lid": "COOKWARE", "sealed pot": "COOKWARE", "steamer": "COOKWARE", "water bath": "APPLIANCE", "lid": "COOKWARE",
    "sealed container": "CONTAINER", "sealed bag": "CONTAINER", "foil": "MATERIAL", "string": "MATERIAL",
    "brush": "UTENSIL", "grater": "UTENSIL", "ladle": "UTENSIL", "sifter": "UTENSIL", "skewer": "UTENSIL",
    "whisk": "UTENSIL",
}
ALIASES = {"slow cooker": ["crockpot", "crock pot", "crock-pot"], "hob": ["stove", "stovetop", "burner"],
           "microwave oven": ["microwave"], "barbecue": ["bbq"], "pan": ["frying pan", "skillet"]}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main() -> int:
    procs = defaultdict(set)
    src = defaultdict(set)
    with (ROOT / "ledgers/process/proc_v0.csv").open() as fh:
        for r in csv.DictReader(fh):
            for part in re.split(r"\s*(?:/|\+| or )\s*", r["encodes_tool"]):
                if part:
                    procs[part].add(r["proc_id"])
                    src[part].add("proc_v0.encodes_tool")
    with (ROOT / "ledgers/process/recipedb_term_map_v0.csv").open() as fh:
        for r in csv.DictReader(fh):
            if r["term_class"] == "TOOL":
                name = {"crockpot": "slow cooker"}.get(r["recipedb_term"], r["recipedb_term"])
                src[name].add("RecipeDB process vocabulary (Bagler 2022, Table S2)")
                procs.setdefault(name, set())
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from culinarystate.decision.core import tool_requirements
    for p, need in tool_requirements().items():
        for part in re.split(r"\s*(?:/|\+| or )\s*", need):
            part = part.strip()
            if part:
                procs[part].add(p)
                src[part].add("decision.core definitional requirement")
    rows = []
    for name in sorted(procs):
        rows.append({"tool_id": f"TOOL-{slug(name)}", "label": name, "aliases": "|".join(ALIASES.get(name, [])),
                     "kind": KIND.get(name, "UNKNOWN"), "process_compatibility": "|".join(sorted(procs[name])),
                     "material": "UNKNOWN", "geometry": "UNKNOWN", "capacity": "UNKNOWN",
                     "heat_source_compatibility": "UNKNOWN", "physical_implications": "UNKNOWN",
                     "safety_warning_ids": "", "source": "; ".join(sorted(src[name])), "status": "PROPOSED"})
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} TOOL- records; kinds:", {k: sum(1 for r in rows if r['kind'] == k) for k in sorted({r['kind'] for r in rows})})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
