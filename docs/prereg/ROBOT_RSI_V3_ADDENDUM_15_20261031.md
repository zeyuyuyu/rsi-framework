# Prereg v3, addendum 15: LIBERO-Goal main arms start before the addendum-11 rule is read; platform split

Committed 2026-10-31 (~04:30Z), before any main-arm run starts. No v3 run has read a test result.

## Early start

The CVPR deadline (register 11-10, paper 11-16) does not allow waiting for the addendum-11 rule (read on
2026-11-01 from `a8_oftg_curve_grpo_s1`). The main arms of addendum 14 therefore start as soon as the Yangquan pool
is staged. They run and are reported whatever the rule says. If the rule fails (the cavin seed-1 D is below -1, so
the mean is below +3), they are reported as main arms run on a recipe that missed its pre-set pilot bar. The arms,
seeds, program and bars of addendum 14 are unchanged.

## Platform split (each comparison stays on one platform)

* **Yangquan pool** (16 x A800-SXM4-80GB, Baidu image with torch 2.8 and the `vla312-r3` venv, run dirs on the
  pool CFS; `run_vla4.sh`): `fixed`, `full`, `onebig`, `nonrec`, `shuffled` x seeds 1-3, which is 15 runs, all in
  one wave. Run names are `yq_oftg_<arm>_s<seed>` (`mkplans_vla.py goal_main grpo yq`).
* **cavin A800** (the `openvla` env stack, src5): `llm` and `fixed` x seeds 1-3, 6 runs. The `llm` arm needs the
  gateway key, which stays on cavin only. It is never written to the shared Yangquan CFS or to BOS.
  Run names are `a8_goalmain_<arm>_s<seed>` (`scripts/a800/mkoft_goal_main.py`).

The two stacks score the same weights differently, as LIBERO-10 SFT showed: 14.6% versus 18.6% across platforms.
So every bar is computed within one platform:

| bar | platform |
|---|---|
| R4 `full - fixed`, R5 best-of(`fixed`, `full`) by gate minus `onebig`, R2 `fixed - shuffled`, R3 `fixed - nonrec` | Yangquan |
| R4-llm `llm - fixed` | cavin, against cavin's own `fixed` |

`llm` against the Yangquan arms is descriptive only.

## cavin GPU order

`vla3_pilot_l10_grpo` (the M2 GRPO pilot) has finished one round in two days and is superseded by the M2 plan in
addendum 10. It is stopped to free a GPU, and its records are kept. The free GPUs then take, in order: `llm` s1,
`fixed` s1, `llm` s2, `fixed` s2, `llm` s3, `fixed` s3, as the pilots now running finish. The addendum-11 rule run
(`a8_oftg_curve_grpo_s1`) is never preempted.

Amendment (2026-10-31 ~05:00Z, user: "the core is to prove RSI"). Every robot result so far is meta level off (pure
on-policy RL). The cavin GPUs therefore go to the RSI arms first. Two non-core pilots stop now and are reported
as stopped early, with their records kept: `a8_oftg_curve_bct_s1` (BC temperature fix, addendum 12) and
`vla3_pilot_l10_bc_shuf` (M2 shuffled control, addendum 10). `a8_oftg_curve_grpo_s1` (the addendum-11 rule run)
and `a8_ofts_curve_grpo_s0` (Spatial, addendum 13) keep running. Queue order on cavin: `llm` s1, `fixed` s1, `llm` s2,
`fixed` s2, `llm` s3, `fixed` s3. Added to the analysis, fixed now: whether meta-level edits compound. That means the
per-round acceptance rate of proposed procedures and the gate gain of accepted edits as a function of the round,
for `llm` and `full`.
