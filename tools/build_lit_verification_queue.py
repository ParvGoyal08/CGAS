r"""
K8 — order the literature candidates for human verification (no values touched).

    .venv/bin/python tools/build_lit_verification_queue.py [n]

Priority (deterministic): caption names retention/retained/true retention (3) > loss/degradation/
change (2) > a cooking process (1). At most 12 cells per paper; papers rotate within a family
(best priority first); families rotate globally — so the first ≥ 40 verified rows span the 12
anchor families instead of one paper (v4.0 AI5).
Writes ledgers/literature/verification_queue_v0.csv (first n rows, default 200).
"""
from __future__ import annotations

import csv
import pathlib
import re
import sys
from collections import defaultdict, deque

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "ledgers/literature/candidates_v0.csv"
OUT = ROOT / "ledgers/literature/verification_queue_v0.csv"
P3 = re.compile(r"retention|retained|true retention|apparent retention|retention factor", re.I)
P2 = re.compile(r"\bloss(es)?\b|degradation|decrease|reduction|change", re.I)
P1 = re.compile(r"cook|boil|steam|fr(y|ie)|roast|bak|microw|blanch|grill|sous|pressure", re.I)


def prio(caption: str, col: str) -> int:
    t = f"{caption} {col}"
    return 3 if P3.search(t) else 2 if P2.search(t) else 1 if P1.search(t) else 0


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    rows = list(csv.DictReader(SRC.open()))
    per_paper_cap = 12
    fam_cells = defaultdict(list)                       # family → cells, best first, ≤ cap per paper
    by_fp = defaultdict(lambda: defaultdict(list))
    for r in rows:
        p = prio(r["caption"], r["col_header"])
        if p:
            by_fp[r["family"]][r["pmcid"]].append((-p, int(r["row_index"]), int(r["col_index"]), r))
    for f, papers in by_fp.items():
        qs = {pm: deque(sorted(c, key=lambda x: x[:3])[:per_paper_cap]) for pm, c in papers.items()}
        order = deque(sorted(qs, key=lambda pm: qs[pm][0][0]))          # papers with best priority first
        while order:
            pm = order.popleft()
            fam_cells[f].append(qs[pm].popleft())
            if qs[pm]:
                order.append(pm)
        fam_cells[f].sort(key=lambda x: x[0])                            # stable: priority, then paper rotation
    fams = deque(sorted(fam_cells))
    out = []
    while fams and len(out) < n:
        f = fams.popleft()
        negp, _, _, r = fam_cells[f].pop(0)
        out.append({"queue_rank": len(out) + 1, "priority": -negp, **r})
        if fam_cells[f]:
            fams.append(f)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    by_p = defaultdict(int)
    for r in rows:
        by_p[prio(r["caption"], r["col_header"])] += 1
    print(f"candidates {len(rows)}; by priority {dict(sorted(by_p.items()))}; queue {len(out)} rows; "
          f"families in queue {len({r['family'] for r in out})}; papers {len({r['pmcid'] for r in out})}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
