# Prereg v3, addendum 34: Spatial 12 rounds on the A800 node: one-shot RL and the guard-rail gate (seed 0)

Committed 2026-11-12 (~19:30Z; commit time in git) before either run below exists. No test or gate result of these runs exists.

## Why

Addendum 30 registered `yq_ofts_onebig12_s{1,2,3}`, one round of 36 inner steps: the equal-compute RL control of the 12-round Spatial loops. It was to be submitted "only if three cards are free", and it never was, because the Yangquan queue has been full.
- The A800 node has two idle cards and an empty queue.
- Its 12-round pair `a8_spatmain_fixed12_s0` / `a8_spatmain_nonrec12_s0` is complete with finals.
- Addendum 32 tested the guard-rail gate at 12 rounds on Goal only.

## Runs (A800 node, seed 0, source src13 = v32, one card each)

| run | plan |
|---|---|
| `a8_spatmain_onebig12_s0` | `a8_spatmain_fixed12_s0` with `rounds 1, inner_steps 36` (addendum 30's onebig12 definition) |
| `a8_spatmain_guard12_s0` | `a8_spatmain_fixed12_s0` with the guard-rail fields `min_gate_gain -0.05`, `gate_floor 0.05`, `test_all_accepted false` |

Finals are as for the other A800 runs: in-run test, `_rep` (two replicates) and `_fresh`. The read happens once, when both runs and their evaluations exist, if that is before 2026-11-15 12:00Z.

## Use (descriptive; one seed, so no bar is claimed)

Each comparison is paired within the platform against `a8_spatmain_fixed12_s0`, `a8_spatmain_nonrec12_s0` and the A800 reference, and reported on both tests with its CI:
- **FL5-A0**: fixed12 − onebig12. This is addendum 30's R5-long-spatial, at seed 0 only.
- **guard12 − onebig12**: the Spatial counterpart of G3.
- **guard12 − fixed12**: the counterpart of G2.
- **guard12 − start**: the counterpart of G1.

Reader: `fresh_read.py spatial_long12_a8` and `scripts/report/spatial_long12_a8_read.py`, committed before either run has a result.

## Predictions

- fixed12 − onebig12: a tie to −3 (onebig12 led on Goal, −2.7).
- guard12 − onebig12: between −2 and +1.
- guard12 − start: +4 to +7 on fresh scenes.

## Operational notes

- 2026-11-12 19:22:47Z: both runs were queued after this addendum (f659907, 19:22:34Z). They launched at 19:23:18Z on GPUs 0 and 1.
- 21:20:47Z: `a8_spatmain_guard12_s0` failed in round 1, at the training call of its third inner step: CUDA out of memory on GPU 0.
  - Cause: an unrelated job from another project on the same node account started on GPU 0 about 40 minutes earlier and held 35 GB, later 74 GB. That job was not touched.
  - No round of this run had completed, and no gate or test result exists.
  - The run is requeued with `--resume` (queue order 118) and starts when a card frees, on the same plan and source.
- The read deadline is unchanged (2026-11-15 12:00Z). If the run cannot complete by then, it is reported as not read.
