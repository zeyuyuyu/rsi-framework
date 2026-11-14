# Robot RSI v3, addendum 36 (2026-11-14): cost curves and three-evaluation fresh finals for the counted-tuning comparison

Committed before any evaluation named here is submitted. No training; evaluations of checkpoints that already exist.

## Why

The paper compares the self-repairing loop (LLM meta level from the failing BC recipe, `yq_oftgb_llm_harness_s1-3`,
`a8_oftgb_llm_harness_s0`) with one-shot RL on the hand-tuned recipe, counting RL's 21 pilot runs (213.4 GPU-hours
on record; `docs/results/TUNING_COST_20261112.md`). That comparison rests on two endpoints per seed and on one
fresh-scene evaluation per version. Five A800 cards and Yangquan one-card slots are free until the deadline.

- **Part A (cost curves)** scores intermediate versions on the sealed fresh-scene test, so the paper can show success
  against cumulative GPU-hours with the tuning counted.
- **Part B (three-evaluation fresh finals)** scores the two endpoint versions of the comparison twice more on the
  fresh-scene test, so its fresh finals are three-evaluation means like the official finals.

## Part A: points (one fresh-scene evaluation each)

- **Self-repairing loop**: the version retained after each of rounds 1-5 (round 6 is already read).
  - s0 (A800): r01c1, r02c1, r03c1, r04c0, r05c1
  - s1: r01c1, r02c1, r03c0, r04c0 (round 5's version r05c1 is round 6's)
  - s2: r01c1, r02c1, r03c1, r04c1, r05c0
  - s3: r01c0, r03c0, r04c1, r05c0 (round 2 kept r01c0)
- **One-shot RL, 36 blocks** (`yq_oftg_onebig12_s1-3`): after blocks 6, 12, 18, 24 and 30 (`r01c0-i5`, `-i11`, `-i17`, `-i23`, `-i29`); block 36 is already read.
- **One-shot RL, 18 blocks**: s0 (A800, `a8_goalmain_onebig_s0`) after blocks 6 and 12 (`r01c0-i5`, `-i11`); s1's single candidate `r01c0`, which the gate refused (its registered version is the start), as the end of its trajectory.
- 29 Yangquan jobs and 7 A800 evaluations.

**Cost axis.** Self-repairing loop: the run's reserved card-hours (Yangquan 89.6 / 206.0 / 58.8; A800 s0 103.6, a lower bound) apportioned by the backend seconds recorded through each round (`round-NN.json`). One-shot RL: 213.4 plus the run's card-hours apportioned by blocks (k/36 or k/18). The start (60.0%) sits at 0 for the loop and at 213.4 for RL.

## Part B: two more fresh-scene evaluations (`--replicates 2`)

The versions of the registered comparison: the loop's round-6 version (s0 r06c0, s1 r05c1, s2 r06c0, s3 r06c1) and RL's 18-block retained version (s0 r01c0, s1 n0, s2 r01c0, s3 r01c0). Six Yangquan jobs, two A800 evaluations. With the registered evaluation each version then has three.

## Code, names, reading

- Sources as for the registered evaluations: Yangquan `rsi_src_v30` (its fresh-eval scores any node with a receipt), A800 `src13` (v32). Checkpoint `Haozhan72/Openvla-oft-SFT-libero-goal-traj1`.
- Names: Part A `<run>_cc_<node>`, Part B `<run>_fresh23`.
- Reader `scripts/report/cost_curve_read.py`, committed before any of these results is fetched.
- Reported: Part A as a figure for Finding 6, every point shown, no fitted line; Part B beside the registered one-evaluation estimate. Finding 6 states both. Descriptive: no bar.
- Evaluations not complete by 2026-11-15 14:00Z are reported as missing.

## Predictions, written before any submission

- Part A: the loop's fresh success climbs from 60 to 61-64 over rounds 1-5. RL-36 is near 61 at block 18 and reaches the loop's round-6 level (63.5) between blocks 24 and 30, that is at about 225-235 GPU-hours with the tuning counted.
- Part B: the three-evaluation estimate of loop − RL (18 blocks) on fresh scenes is +1 to +3, CI above zero with probability about 0.6.

## Operational notes

- 2026-11-14 05:5xZ: the 35 Yangquan jobs were submitted (one card each, `rsi_src_v30`); job ids are in `scripts/baidu/jobs_yq.tsv`. The nine A800 evaluations were queued as entries 129-137 on `src13`.
- The reader `scripts/report/cost_curve_read.py` was committed after the submissions and before any of their results was fetched; `--check` lists the missing evaluations and prints no success number.
