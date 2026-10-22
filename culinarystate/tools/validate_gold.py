r"""
P4 — validate gold YAML files: JSON-schema structure, then semantic replay through the state engine.
    .venv/bin/python tools/validate_gold.py [paths or dirs ...]   (default: gold/)
Files under any folder named 'invalid' must FAIL (they document rejected structures); every other file must PASS.
"""
from __future__ import annotations

import json
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from culinarystate.state_graph.gold import GoldError, compile_gold  # noqa: E402

SCHEMA = json.loads((ROOT / "docs/annotation/gold_schema.json").read_text())


def structural(doc) -> list[str]:
    try:
        import jsonschema
    except ImportError:                                   # minimal fallback: required keys only
        return [f"missing {k}" for k in SCHEMA["required"] if k not in (doc or {})]
    return [e.message for e in jsonschema.Draft202012Validator(SCHEMA).iter_errors(doc)]


def check(path: pathlib.Path) -> tuple[bool, str]:
    try:
        doc = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        return False, f"yaml: {str(e).splitlines()[0]}"
    errs = structural(doc)
    if errs:
        return False, "schema: " + "; ".join(errs[:3])
    try:
        g = compile_gold(doc, str(path))
    except GoldError as e:
        return False, f"replay: {e}"
    return True, f"{len(g.events)} events, {len(g.graph.entities)} lots"


def main(argv) -> int:
    targets = [pathlib.Path(a) for a in argv] or [ROOT / "gold"]
    files = sorted(f for t in targets for f in ([t] if t.is_file() else t.rglob("*.yaml")))
    bad = 0
    for f in files:
        ok, msg = check(f)
        expect_ok = "invalid" not in f.parts
        good = ok == expect_ok
        bad += not good
        print(f"{'OK ' if good else 'BAD'} {'pass' if ok else 'fail'} (expected {'pass' if expect_ok else 'fail'}) "
              f"{f.relative_to(ROOT)} — {msg}")
    print(f"\n{len(files) - bad}/{len(files)} as expected")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
