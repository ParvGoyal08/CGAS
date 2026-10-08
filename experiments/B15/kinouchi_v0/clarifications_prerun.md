# Pre-run clarifications — Kinouchi reproduction (written 2026-10-09, BEFORE any run)

`prereg.md` is frozen and unchanged; see `FREEZE.md`. These notes resolve wording that the frozen text leaves open. They are written before any simulation output exists, and the first run is committed after this file.

| # | Question | Resolution |
|---|---|---|
| C1 | AC-2 verdict basis | The pass/fail uses the **5-seed mean curve** of 1 − F_Total(t). Per-seed γ values are reported beside it |
| C2 | The time axis t | t = R(t), the number of recipes after each step (t = R0+1 … T); F_Total is defined over all R(t) recipes |
| C3 | "Rises then decays" (AC-2) | The argmax of the seed-mean 1 − F_Total is not the first point, and the last value is below the maximum |
| C4 | Units of eq. (1) in AC-1 | f is a **fraction** of recipes (published C = 8.7 gives f(1) ≈ 0.63) and is compared with the simulated fraction f(r) defined in the prereg. If the paper's f were counts, AC-1 would be incomparable; this is recorded as a risk, not changed after the run |
| C5 | AC-3(b) "founder ingredient" | an ingredient present in any of the R0 initial recipes |
| C6 | Variants that get every AC | primary; IC-b; A3 = `T_steps`; A4 = `without_replacement`. Each is a one-factor change from the primary. AC-4 compares the primary with the N1 ablation (`selection="always"`) |
| C7 | Heavy-tail table T2 | computed on seed 0 of the primary run (counts of recipes per ingredient), with 1,000 bootstraps |
