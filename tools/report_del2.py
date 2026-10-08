r"""
P8 — DEL-2 results + gate verdicts from a finished run (card §U–§X applied mechanically).

    .venv/bin/python tools/report_del2.py experiments/DEL2/runs/<run-id>

Seed aggregation (not specified in the frozen card; chosen BEFORE viewing the full run and
disclosed in DEC-032): a gate passes only if it passes in EVERY seed; every seed is shown.
Writes <run>/results.md and <run>/verdicts.json.
"""
from __future__ import annotations

import json
import pathlib
import sys

MODELS = ("D0", "D1", "D2", "D3", "D4", "D5", "D5-noproc", "D7", "D7-noproc", "MF-biased")
MIN_GROUPS = 30            # card §X
D7_REL_TOL = 0.10          # card §U (AM5)


def f(x, d=2):
    return f"{x:.{d}f}"


def main(run: pathlib.Path) -> int:
    m = json.loads((run / "metrics.json").read_text())
    S = m["splits"]
    seeds = sorted(S["pair"])
    v = {"run": run.name, "card_sha256": m["card_sha256"], "quick": m["quick"], "seed_rule": "all seeds must pass"}

    def paired(split, key):
        return [S[split][s]["_paired"][key] for s in seeds]

    def underpowered(split):
        return [S[split][s]["_groups"] < MIN_GROUPS for s in seeds]

    for fam in ("D5", "D7"):
        key = f"{fam}-noproc minus {fam} (H2)"
        per = {sp: [p["ci"][0] > 0 for p in paired(sp, key)] for sp in ("pair", "ingredient")}
        if any(underpowered("pair")) or any(underpowered("ingredient")):
            verdict = "UNDERPOWERED"
        elif all(per["pair"]) and all(per["ingredient"]):
            verdict = "SUPPORTED"
        elif all(p["ci"][1] < 0 for sp in ("pair", "ingredient") for p in paired(sp, key)):
            verdict = "NEGATIVE (process features hurt)"
        else:
            verdict = "NOT SUPPORTED (CI includes 0 in ≥1 seed/split)"
        v[f"H2_{fam}"] = {"verdict": verdict, "per_seed_ci_gt0": per,
                          "groups": {sp: [S[sp][s]["_groups"] for s in seeds] for sp in ("pair", "ingredient")}}
    d57 = paired("pair", "D5 minus D7 (D7 promotion)")
    ing_ratio = [S["ingredient"][s]["D7"]["mae"] / S["ingredient"][s]["D5"]["mae"] for s in seeds]
    if any(underpowered("pair")) or any(underpowered("ingredient")):
        d7v = "UNDERPOWERED → NOT PROMOTED (card §X: the ingredient harm check cannot be established)"
    elif all(p["ci"][0] > 0 for p in d57) and all(r <= 1 + D7_REL_TOL for r in ing_ratio):
        d7v = "PROMOTED"
    else:
        d7v = "NOT PROMOTED"
    v["D7_promotion"] = {"verdict": d7v,
                         "pair_ci_gt0_per_seed": [p["ci"][0] > 0 for p in d57],
                         "ingredient_D7_over_D5_per_seed": ing_ratio}
    nc = (m.get("negative_control") or {}).get("D5-noproc minus D5 under permuted processes")
    v["negative_control"] = {"verdict": "NOT RUN in this run"} if nc is None else {
        "verdict": "PASS (advantage gone)" if nc["ci"][0] <= 0 else "FAIL (advantage persists → suspect leakage)", **nc}
    pc = m.get("positive_control")
    v["positive_control"] = {"verdict": "NOT RUN in this run"} if pc is None else {
        **pc, "recovered_share": pc["recovered_on_boil_cells"] / pc["injected_effect"],
        "verdict": "card sets no numeric tolerance — reported for human judgement"}
    (run / "verdicts.json").write_text(json.dumps(v, indent=2))

    L = [f"# DEL-2 results — run `{run.name}`\n",
         f"Card sha `{m['card_sha256'][:16]}…` (unchanged since freeze; `gate.py` G-PREREG). Cells {m['cells']:,}; "
         f"censored at 100: {m['censored_share']:.1%}. Seeds {', '.join(seeds)}. "
         "Primary metric: censor-aware MAE (retention points); 95% CIs from a 2,000-resample grouped bootstrap.\n",
         "**Seed rule (DEC-032):** the card does not say how to combine seeds; a gate passes only if it passes in every seed.\n",
         "## Gate verdicts (card §U–§X)\n",
         f"Held-out groups — pair {S['pair'][seeds[0]]['_groups']}, ingredient {S['ingredient'][seeds[0]]['_groups']} "
         f"(card §X: < {MIN_GROUPS} → underpowered, no claim).\n", "| Gate | Verdict |\n|---|---|",
         f"| H2 — process information helps (D5 family) | **{v['H2_D5']['verdict']}** |",
         f"| H2 — process information helps (D7 family) | **{v['H2_D7']['verdict']}** |",
         f"| D7 promotion (AM5 / G15-9) | **{v['D7_promotion']['verdict']}** |",
         f"| Negative control (permuted processes) | **{v['negative_control']['verdict']}** |",
         ("| Positive control (−20 on boil) | NOT RUN |" if pc is None else
          f"| Positive control (−20 on boil) | recovered {pc['recovered_on_boil_cells']:.1f} of −20 "
          f"({v['positive_control']['recovered_share']:.0%}); spillover on other cells {pc['spillover_on_other_cells']:+.2f} |"), ""]
    for split in ("pair", "ingredient", "process", "random"):
        L.append(f"## Split: {split}\n")
        L.append("| Model | " + " | ".join(f"MAE seed {s} [95% CI]" for s in seeds) + " | IPS-MAE (seed 1) |")
        L.append("|---|" + "---|" * (len(seeds) + 1))
        for mod in MODELS:
            cells = [f"{f(S[split][s][mod]['mae'])} [{f(S[split][s][mod]['ci'][0])}, {f(S[split][s][mod]['ci'][1])}]" for s in seeds]
            ips = S[split][seeds[0]][mod].get("ips_mae")
            L.append(f"| {mod} | " + " | ".join(cells) + f" | {f(ips) if ips is not None else '—'} |")
        L.append("\n| Paired difference (positive = right model better) | " + " | ".join(f"seed {s}" for s in seeds) + " |")
        L.append("|---|" + "---|" * len(seeds))
        for key in S[split][seeds[0]]["_paired"]:
            L.append(f"| {key} | " + " | ".join(
                f"{f(S[split][s]['_paired'][key]['diff'])} [{f(S[split][s]['_paired'][key]['ci'][0])}, {f(S[split][s]['_paired'][key]['ci'][1])}]"
                for s in seeds) + " |")
        cf = S[split][seeds[0]]["_conformal"]
        L.append("\nEmpirical split-conformal (nominal 90%; **no validity claim under shift**, AH4), seed " + seeds[0] + ": " +
                 "; ".join(f"{k} coverage {c['coverage_mean']:.1%} width {c['width_mean']:.1f}" for k, c in cf.items()))
        L.append(f"\nHeld-out groups: {', '.join(str(S[split][s]['_groups']) for s in seeds)}\n")
    p1 = m["propensity"]["spec1"]
    L += ["## SX-13-04 propensity (overlap)\n",
          f"Universe {p1['universe']:,} food × process pairs, observed {p1['observed']}; propensity min {p1['p_min']:.3f}, "
          f"median {p1['p_median']:.3f}; clipped at 0.05: {p1['clipped_share']:.1%}. The propensity is a modelling assumption, "
          "not known truth (card).\n",
          "## Limits (card §Y)\n",
          "US data compiled 1975–2007; preparation categories only, no temperatures. Results do **not** imply "
          "condition-independent process effects (AM1). 143 of 270 codes sit in USDA duplicate-imputation clusters, which are "
          "grouped before splitting.\n"]
    (run / "results.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main(pathlib.Path(sys.argv[1])))
