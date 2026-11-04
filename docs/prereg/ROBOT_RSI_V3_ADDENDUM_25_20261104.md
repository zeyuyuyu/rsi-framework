# Prereg v3, addendum 25: scheduling — the seed-0 Goal block moves to cavin; the Yangquan queue is reordered

Committed 2026-11-04 ~17:30Z. Operational only: no arm, recipe, bar or read rule changes. No run named here has
scored a round beyond its starting policy (n0) at the time of writing.

## Why

Addendum 24's `llm_harness` arms (its primary) and `full` s2-3 are queued on Yangquan behind runs that occupy all
16 cards until about 2026-11-05 08:00Z. cavin has 5 free GPUs. Addendum 14 pairs arms within a seed, so a seed's
four arms must share a platform, but different seeds may sit on different platforms.

## Changes

* **Seed-0 Goal block (addendum 23) moves to cavin.** `yq_oftg_{fixed,nonrec,shuffled,onebig}_s0` are stopped
  (each about 2 h in, round 1 unscored) and replaced by `a8_goalmain_{fixed,nonrec,shuffled,onebig}_s0` on cavin:
  the cavin Goal `fixed` plan of seeds 1-3 with `engine.seed = 0` and the arm's one engine field (`recursive`
  false / `feedback` shuffled / `rounds` 1 + `inner_steps` 18), source src5, the tree the cavin Goal `fixed`
  arms ran on (their job files). R2, R3
  and R5 remain seed-averaged over seeds 0-3; seed 0's comparison is paired within cavin. Seeds 1-3 stay on
  Yangquan. The yq seed-0 job ids are kept in `jobs_yq.tsv` with their stop time.
* **`yq_oftgb_fixed_s3` is stopped** (about 1.5 h in, round 1 unscored) and resubmitted with `--resume`, so it
  continues its own state; it queues behind the five addendum-24 runs now able to start.
* Nothing else is touched. Test reads are unchanged: the Goal read-once waits for the cavin seed-0 block and the
  addendum-22 runs; addendum 24 is read when its nine runs have `report.json`.
