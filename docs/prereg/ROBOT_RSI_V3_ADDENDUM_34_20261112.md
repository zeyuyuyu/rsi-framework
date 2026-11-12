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

## Amendment 1 (2026-11-12 ~23:00Z, before any run named here exists): Yangquan seeds 1-3

Yangquan now runs only four of our jobs, on six cards. Two changes follow.

**Addendum 30's onebig12 runs are submitted.** Addendum 30 registered `yq_ofts_onebig12_s{1,2,3}` "only if three cards are free", and that condition now holds.
- Plans: as written by `mkplans_vla.py yq_spatial_long12` (1 round × 36 inner steps).
- Source: v30, like the `fixed12` / `nonrec12` runs they are compared with.
- FL5 (fixed12 − onebig12) is read as addendum 30 registered it.

**New runs `yq_ofts_guard12_s{1,2,3}`.** These are the `yq_ofts_fixed12_s<seed>` plans with the guard-rail fields `min_gate_gain -0.05`, `gate_floor 0.05`, `test_all_accepted false`, as addendum 32 did on Goal, on source v32. The claims are the Spatial counterparts of addendum 32 Part A, on seeds 1-3, with fresh scenes primary and the official test beside them. A0 (the runs above) is reported alongside when complete.

| claim | comparison | bar (fresh primary; official beside) |
|---|---|---|
| G2s | guard12 − fixed12 | ≥ +2, CI > 0 |
| G1s | guard12 − initial | ≥ +5, CI > 0 (official: R1 rule) |
| G3s | guard12 − onebig12 | CI reported; non-inferior if lower bound > −2 |

- **When**: read once, when the nine Yangquan runs (fixed12, onebig12 and guard12 × 3 seeds) have finals and fresh-scene evaluations, if that is before 2026-11-15 12:00Z. Otherwise they are reported as not read.
- **Predictions**: G1s +5 to +7; G2s 0 to +3; G3s between −2 and +1. These are the same ranges as on Goal.
- **Readers**: committed before any result of these runs exists.
- 2026-11-12 22:49:19-22:49:29Z: `yq_ofts_onebig12_s1-3` (v30) and `yq_ofts_guard12_s1-3` (v32) were submitted to Yangquan, after amendment 1 (856e5ab, 22:48:46Z).
  - The guard12 plans are the fixed12 plans plus the three guard-rail fields, uploaded to BOS.
  - The onebig12 plans were re-uploaded from the files `mkplans_vla.py yq_spatial_long12` wrote under addendum 30, because the uploader's key cannot read BOS back to verify them.
  - `submit_rep_yq.sh` maps `yq_ofts_guard12_*` to v32 for replicates.
- Readers `fresh_read.py spatial_guard12` and `spatial_guard12_read.py` were committed before any result. They were checked on a scratch root of already-read runs, where the values equal earlier reads.
- `scripts/baidu/close_loop_yq.sh` takes over the Yangquan close-out when the conductor's loop ends (about 2026-11-14 09Z) and runs until 2026-11-15 13:00Z.
- 22:51:14Z: `yq_ofts_guard12_s3` failed about 90 s after starting. Its entry script's curl download of the source tarball was reset by the peer (`OpenSSL SSL_read: Connection reset by peer`), before any training. It was resubmitted unchanged about 23:00Z.
- 22:54Z: on the A800 node, `a8_spatmain_guard12_s0` resumed by hand on GPU 3 (the user cleared that card on 2026-11-12). The runner excludes GPU 3, so the launch copies the runner's own procedure: the plan with the assigned GPUs written to `queue/plans/`, `run_libero --resume` started in its own session, and a reservation entry for the card. The resume check compares the engine plan, not the GPU fields.
