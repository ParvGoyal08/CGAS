r"""
DEL-3 inter-annotator agreement for one recipe (P4).

    PYTHONPATH=src python3 tools/del3_agreement.py gold/<recipe>.A.yaml gold/<recipe>.B.yaml [--json out.json]

Both files must be independent annotations of the same recipe (guideline v0 §6).
"""
from __future__ import annotations

import json
import sys

from culinarystate.state_graph.agreement import agreement
from culinarystate.state_graph.gold import GoldError, load_gold


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    try:
        a, b = load_gold(argv[1]), load_gold(argv[2])
    except GoldError as exc:
        print("INVALID GOLD:", exc)
        return 1
    r = agreement(a, b)
    print(f"recipe {r['recipe_id']}  annotators {r['annotators'][0]} vs {r['annotators'][1]}  "
          f"lots matched {r['lots']['matched']}/{r['lots']['union']}")
    for k in ("event_f1", "edge_f1", "merge_split_f1"):
        print(f"  {k:<22} P={r[k]['precision']:.3f} R={r[k]['recall']:.3f} F1={r[k]['f1']:.3f}")
    for k in ("quantity_agreement", "allocation_agreement", "field_agreement"):
        print(f"  {k:<22} {r[k]:.3f}")
    for side in ("a_only", "b_only"):
        for e in r["merge_split_f1"][side]:
            print(f"  [{side}] {e}")
    if "--json" in argv:
        out = argv[argv.index("--json") + 1]
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(r, fh, indent=2, ensure_ascii=False)
    gate = r["merge_split_f1"]["f1"] >= 0.80
    print(f"guideline gate (merge/split F1 ≥ 0.80, PROPOSED): {'PASS' if gate else 'REVISE GUIDELINE'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
