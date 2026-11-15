# Robot RSI v3, addendum 37 (2026-11-15): three-evaluation finals for the counted-tuning comparison, cost-curve points of the continued loop, and seed 0 continued on the A800 node

Committed before anything named here is submitted. Written after addendum 35's interim read (2026-11-14) was known; everything below is reported as descriptive, beside the registered reads, and none of it changes addendum 35's claims, cut-off or primary read. Deadline for every read here: 2026-11-16 00:00Z; anything not complete then is reported as missing.

## Why

Five A800 cards and Yangquan one-card slots are free until the paper deadline. Three additions sharpen the comparison the paper rests on (the loop against tuned RL with RL's 213.4 GPU-hours of pilots counted):

## Part A: three-evaluation fresh finals for E1 and E2 (Yangquan)

Two more fresh-scene evaluations (`--replicates 2`) of each version in addendum 35's comparison, so each has three like the official finals:
- tuned RL, 36 blocks: `yq_oftg_onebig12_s{1,2,3}` retained `r01c0`, as `<run>_fresh23` (source v30, as its registered evaluation);
- the continued loop's final versions: seed 2 `r08c0` and seed 3 `r07c0` (these are their final versions unless round 11 of seed 3 completes and is kept before 10:00Z, in which case its final node is used), as `yq_oftgbx_ext_s{2,3}_fresh23`; seed 1's final node after the 10:00Z cut-off, as `yq_oftgbx_ext_s1_fresh23` (source v34, `--interim`);
- tuned RL, 18 blocks, already has three (addendum 36 part B).
E1 and E2 are then also reported with three-evaluation fresh finals, beside addendum 35's one-evaluation reads.

## Part B: cost-curve points of the continued loop (Yangquan)

One fresh-scene evaluation of each version the continued loop kept between its interim and final versions, for the cost figure: seed 1 `r11c0`, `r12c0` (and `r13c0` if it is not seed 1's final node), seed 2 `r07c0`; as `yq_oftgbx_ext_s<n>_cc_<node>` (v34, `--interim`). Cost axis: round-6 cost plus the continuation job's card-hours up to the round that kept the version.

## Part C: seed 0 continued on the A800 node

`a8_oftgb_llm_harness_s0` (seed 0's self-repair run, LLM meta level, six rounds) is continued exactly as addendum 35 continued seeds 1-3: `--extend-from`, plan = the run's plan with `engine.rounds 24`, `candidates_per_round 1`, `min_gate_gain -0.05`, `gate_floor 0.05`, `test_all_accepted false`, `meta {"proposer": "fixed"}`; source = the repository's `rsi/` at this commit (identical to v34's `rsi/`), unpacked on the node as `src14`; four cards (rollouts on all, training on the first).
- Budget: seed 0's counted RL cost is 213.4 + 14.3 = 227.7 GPU-hours (18 blocks, one card); its round-6 cost is at least 103.6, so at most 124 card-hours remain; four cards until the stop below use at most about 60.
- Stop: 2026-11-15 20:00Z (process stopped by its exact pid). The version kept then is evaluated: official test with `--replicates 3`, fresh scenes with `--replicates 3`, both `--interim`.
- Compared with tuned RL, 18 blocks, seed 0 (`a8_goalmain_onebig_s0`: official three-evaluation final; fresh three evaluations from addendum 36), within the platform. There is no 36-block RL run for seed 0, so seed 0 enters E2 only.
- Disclosed: seed 0's round-6 result (fresh 67.0 against RL's 64.9) was known when this part was decided, so it is reported beside the registered three seeds and never pooled into addendum 35's claims.

## Reading

Reader `scripts/report/addendum37_read.py`, committed before any of these results is fetched. Same statistics as addendum 35 (seed-averaged per-episode paired bootstrap, 10,000 draws).

## Predictions, written before submission

- Part A: three-evaluation E1 stays negative while seed 3 keeps `r07c0` (about −2, CI below 0); three-evaluation E2 stays positive (+2 to +3, CI above 0).
- Part B: seed 1's kept versions after round 9 score 67-70 on fresh scenes.
- Part C: one to three more rounds by the stop; seed 0's fresh score moves by −1 to +2 from 67.0.

## Operational notes

- 2026-11-15 ~04:50Z: part A and B jobs submitted on Yangquan (ids in `scripts/baidu/jobs_yq.tsv`).
- Part C, before launch: when the four cards were checked, GPUs 2, 4 and 5 had been taken again by another project's jobs. Part C therefore runs on two cards, GPU 1 and GPU 3 (GPU 3 shared with an unrelated 4.5 GB process, as on 11-12); rollouts on both, training on GPU 1. Everything else as above; fewer rounds are expected by the stop.
- 2026-11-15 ~05:45Z, part C: GPUs 4 and 7 were released for this study by the session that held them (until 11-16 01:00Z). The 36-block RL run for seed 0 that would give seed 0 an E1 comparator needs about 16 h of rollouts plus 10 h of single-card training (from `a8_goalmain_onebig_s0`: 8.0 h rollouts + 5.1 h training for 18 blocks), so it cannot finish before the deadline and is not started. Instead part C is restarted on four cards (GPUs 1, 3, 4, 7) with `--resume`: process 1728010 is stopped by its pid during its first continued round (about 40 minutes in), and that round is rerun from its start with the same seeds. Nothing else changes; the stop stays 2026-11-15 20:00Z.
