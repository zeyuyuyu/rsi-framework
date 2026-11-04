# Prereg v3, addendum 22: launching the `nonrec` and `shuffled` Goal arms (R2, R3)

Committed 2026-11-04 ~15:10Z, before any `nonrec` or `shuffled` Goal run starts.

## Why now

Addendum 14 ordered the LIBERO-Goal main arms: `full`, `llm`, `onebig`, `fixed` first, "then `nonrec` and
`shuffled`". The first group is done (the last arm, `yq_oftg_llm_harness_s2`, is in its final round). `nonrec` and
`shuffled` were never launched. They are the two arms that answer "RSI or just RL" without the meta level:

* **R3 recursion:** `fixed` − `nonrec` ≥ +2.0, CI excludes 0. `nonrec` generates every round's experience with the
  initial policy, so the loop is not recursive.
* **R2 verifier:** `fixed` − `shuffled` ≥ +3.0, CI excludes 0. `shuffled` permutes success labels within each case.

Both bars are unchanged from prereg v3. The seed-averaged, per-episode paired bootstrap is as in addendum 14.

## What is launched

`yq_oftg_nonrec_s{1,2,3}` and `yq_oftg_shuffled_s{1,2,3}`: the plans written by `mkplans_vla.py goal_main grpo yq`
on 2026-10-31 together with the other Goal arms. Each differs from `yq_oftg_fixed_s<seed>` in exactly one engine
field (`recursive: false`, or `feedback: "shuffled"`). Same source (rsi_src_v17), same Yangquan queue, same
53-hour limit and resume rule (addendum 18). Tests sealed; they are read with the Goal read-once.

## Disclosures

* The Goal read-once has not happened: no Goal main arm's test file has been opened.
* The v2 study (addendum 21) read its own test on 2026-11-04 ~06:05Z (`docs/results/M2_V2_20261104.md`). It uses
  the same 500 official LIBERO-Goal episodes, so the initial policy's test score (57.2-60.0 across runs) is known.
  No `fixed`, `nonrec` or `shuffled` policy was involved in that read.
* The launch is late, not changed: the arms, recipe and bars are those registered on 2026-10-29/31.
