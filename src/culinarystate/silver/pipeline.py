r"""
P7 — Silver data factory (PREPARED, NOT LAUNCHED). Recipes → multi-pass LLM annotation → DEL3-GOLD-v0 YAML →
deterministic validation (schema + engine replay) → audit. Scale only by gated stages:

    1k → audit (GO/REPAIR/STOP) → 5k → audit → 10k → decision.   Beyond 10k is refused here (master plan: only
    after Gold/schema/quality gates pass, as a separate approved change).

A real run needs: a licensed source adapter (RecipeDB once access is granted), an approved LLM budget (H3), and for
stages after the first, a GO audit record of the previous stage (silver/audits/stage_<n>.json).
"""
from __future__ import annotations

import json
import pathlib
import re
import time
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional, Protocol

import yaml

from ..ner.scorer import _shingles
from ..state_graph.agreement import agreement
from ..state_graph.gold import GoldError, compile_gold

ROOT = pathlib.Path(__file__).resolve().parents[3]
STAGES = (1000, 5000, 10000)
AUDITS = ROOT / "silver/audits"


# ------------------------------------------------------------------ gates
class StageGateError(RuntimeError):
    pass


def check_stage(n: int, audits: pathlib.Path = AUDITS) -> None:
    if n not in STAGES:
        raise StageGateError(f"stage size must be one of {STAGES}; beyond 10k needs a separate approved change")
    i = STAGES.index(n)
    if i == 0:
        return
    prev = audits / f"stage_{STAGES[i - 1]}.json"
    if not prev.exists():
        raise StageGateError(f"stage {n} needs the audit of stage {STAGES[i - 1]} ({prev})")
    d = json.loads(prev.read_text())
    if d.get("decision") != "GO":
        raise StageGateError(f"stage {STAGES[i - 1]} audit decision is {d.get('decision')!r}, not GO")


# ------------------------------------------------------------------ adapters
class SourceAdapter(Protocol):
    name: str
    licence: str

    def iter_recipes(self) -> Iterator[dict]:          # {recipe_id, title, ingredients: [str], steps: [str]}
        ...


@dataclass
class FixtureAdapter:
    """Our own fixture/handbook texts — for dry runs and tests only (FIX- ids never enter any benchmark)."""
    name: str = "fixtures"
    licence: str = "project-authored"
    folders: tuple = ("gold/fixtures", "gold/hard_examples", "gold/UNKNOWN_examples")

    def iter_recipes(self):
        seen = set()
        for d in self.folders:
            for f in sorted((ROOT / d).glob("*.yaml")):
                doc = yaml.safe_load(f.read_text())
                if doc["recipe_id"] in seen:
                    continue
                seen.add(doc["recipe_id"])
                yield {"recipe_id": doc["recipe_id"], "title": doc["recipe_id"], "ingredients": [],
                       "steps": [s.get("text", "") for s in doc["steps"]], "_gold": doc}


class RecipeDBAdapter:
    name, licence = "recipedb", "PENDING — written terms from Prof. Bagler / CoSyLab"

    def iter_recipes(self):
        raise NotImplementedError("RecipeDB access not granted yet (BLOCKED_EXTERNAL); implement once the API/bulk format is known")


# ------------------------------------------------------------------ annotation
PROMPTS = ROOT / "prompts/silver"


def build_prompt(recipe: dict, pass_name: str) -> str:
    tpl = (PROMPTS / f"{pass_name}.md").read_text()
    text = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(recipe["steps"]))
    return tpl.replace("{{RECIPE_ID}}", recipe["recipe_id"]).replace("{{STEPS}}", text)


def extract_yaml(text: str) -> Optional[dict]:
    m = re.search(r"```(?:yaml)?\n(.*?)```", text, re.S)
    try:
        return yaml.safe_load(m.group(1) if m else text)
    except yaml.YAMLError:
        return None


@dataclass
class Tracker:
    calls: int = 0
    seconds: float = 0.0
    prompt_chars: int = 0
    reannotations: int = 0
    failures: dict = field(default_factory=dict)

    def as_dict(self):
        return {"calls": self.calls, "seconds": round(self.seconds, 2), "prompt_chars": self.prompt_chars,
                "reannotations": self.reannotations, "failures": self.failures}


def annotate(recipe: dict, llm, tracker: Tracker, max_attempts: int = 2) -> tuple[Optional[dict], str]:
    """pass 1 (entities) → pass 2 (events YAML) → deterministic validation; one repair pass with the error message."""
    notes = ""
    for attempt in range(max_attempts):
        prompt = build_prompt(recipe, "pass1_entities") + "\n\n" + build_prompt(recipe, "pass2_events")
        if notes:
            prompt += f"\n\nYour previous YAML was rejected by the validator: {notes}\nReturn a corrected YAML document."
            tracker.reannotations += 1
        t0 = time.time()
        out = llm.generate("You annotate recipes into DEL3-GOLD-v0 YAML. Never invent quantities, times or temperatures.",
                           prompt, tag=f"silver:{recipe['recipe_id']}:{attempt}")
        tracker.calls += 1
        tracker.seconds += time.time() - t0
        tracker.prompt_chars += len(prompt)
        doc = extract_yaml(out)
        if not isinstance(doc, dict):
            notes = "output was not a YAML mapping"
            continue
        doc.setdefault("gold_format", "DEL3-GOLD-v0")
        doc["recipe_id"], doc["annotator"] = recipe["recipe_id"], "SILVER"
        try:
            compile_gold(doc, recipe["recipe_id"])
            return doc, "ok"
        except GoldError as e:
            notes = str(e)
    tracker.failures[recipe["recipe_id"]] = notes
    return None, notes


# ------------------------------------------------------------------ audits
def duplicate_families(recipes: Iterable[dict], jaccard: float = 0.8) -> dict:
    """Group near-duplicate recipes (word 5-gram Jaccard ≥ threshold) so a family never straddles splits."""
    items = [(r["recipe_id"], _shingles(" ".join(r["steps"]))) for r in recipes]
    fam = {rid: rid for rid, _ in items}
    for i, (a, sa) in enumerate(items):
        for b, sb in items[i + 1:]:
            if sa and sb and len(sa & sb) / len(sa | sb) >= jaccard:
                fam[b] = fam[a]
    return fam


def vocabulary_growth(docs: list[dict]) -> list[tuple[int, int, int]]:
    """(recipes seen, distinct concepts, distinct process verbs) after each annotated recipe."""
    concepts, procs, out = set(), set(), []
    for n, d in enumerate(docs, 1):
        for s in d.get("steps", []):
            for e in s.get("events") or []:
                for o in e.get("outputs") or []:
                    if o.get("concept"):
                        concepts.add(str(o["concept"]).lower())
                if e.get("process"):
                    procs.add(str(e["process"]).lower())
        out.append((n, len(concepts), len(procs)))
    return out


def silver_vs_gold(silver_doc: dict, gold_doc: dict) -> dict:
    """Agreement of a Silver annotation with a human Gold annotation of the same recipe (event/edge/merge-split F1)."""
    return agreement(compile_gold(gold_doc, "gold"), compile_gold(silver_doc, "silver"))


def run_stage(n: int, adapter, llm, approved_h3: bool, out_dir: pathlib.Path, dry_run_limit: Optional[int] = None) -> dict:
    """dry_run_limit set → no gate check, no H3 needed (fixtures/local model only), writes to out_dir."""
    if dry_run_limit is None:
        if not approved_h3:
            raise StageGateError("a real Silver stage needs H3 (LLM budget) approval")
        check_stage(n)
    tracker, docs = Tracker(), []
    recipes = []
    for k, r in enumerate(adapter.iter_recipes()):
        if k >= (dry_run_limit or n):
            break
        recipes.append(r)
        doc, _ = annotate(r, llm, tracker)
        if doc:
            docs.append(doc)
    out_dir.mkdir(parents=True, exist_ok=True)
    rep = {"stage": n, "adapter": adapter.name, "licence": adapter.licence, "recipes": len(recipes), "valid": len(docs),
           "validity_rate": len(docs) / len(recipes) if recipes else 0.0, "tracker": tracker.as_dict(),
           "duplicate_families": len(set(duplicate_families(recipes).values())),
           "vocabulary_growth_last": vocabulary_growth(docs)[-1] if docs else None, "decision": "PENDING_HUMAN_AUDIT"}
    (out_dir / f"stage_{n}_report.json").write_text(json.dumps(rep, indent=1))
    return rep
