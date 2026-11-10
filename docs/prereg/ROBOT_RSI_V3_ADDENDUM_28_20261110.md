# Prereg v3, addendum 28: the object-level claims on a second suite, LIBERO-Spatial

Committed 2026-11-10 ~04:50Z, before any run named here exists. State at commit time: every registered read is done
(Goal main 11-06, 12 rounds 11-08, meta level v2 11-04/11-06, self-repair 11-09). Both platforms are idle.

## Why

Every arm-level claim so far rests on one suite, LIBERO-Goal. Prereg v3 lists the other suites as in scope ("same
arms where compute allows, `fixed` at least"), and addendum 13 made LIBERO-Spatial a candidate for main arms after its
always-accept GRPO curve cleared the +3 bar at the gate (`a8_ofts_curve_grpo_s0`, D = +7.63 [+4.50, +10.88], one
seed, gate and audit placements, no test). Addendum 20 then ran only a capped meta arm there, with no `fixed`
partner, so Spatial has no arm-level result. The Goal reads left R1, R2 and R3 positive in sign and short of their
bars at six rounds. A second suite is the direct test of whether those directions are a property of the loop or of
one suite. No meta arm is included: the meta level is a registered null on a working recipe (addenda 21, 23), and
this addendum makes no LLM call.

## What is already known about Spatial (disclosed before launch)

* Gate and audit placements only: the addendum-13 curve above (always-accept, so not a gated run).
* One descriptive test read, allowed by addendum 20 am. 1: `a8_spatmain_llm_harness_cap_s1` on the official Spatial
  test, initial 58.6% → final 61.2%, +2.6 [−0.4, +5.6], a single evaluation of one capped meta run. So the cavin
  starting level on the official test (about 58.6%) is known. No `fixed`, `nonrec`, `shuffled` or `onebig` run exists
  on Spatial on either platform, and no Yangquan Spatial test has been run.

## Design (16 runs, the Goal main program with the suite changed)

Checkpoint `Haozhan72/Openvla-oft-SFT-libero-spatial-traj1`, suite `libero_spatial`, tasks 0-9. Program: GRPO,
lr 3e-5, matched ratio, episode-balanced loss, T 1.6, 64 scenes per inner step, 100 steps × batch 64; 6 rounds × 3
inner steps; fresh paired gates (20 placements per task); official test sealed.

| arm | engine | isolates |
|---|---|---|
| `fixed` | 6 rounds, recursive, real feedback | the gated recursive loop |
| `nonrec` | `recursive: false` (every round's practice from the initial policy) | recursion |
| `shuffled` | `feedback: shuffled` (success labels permuted) | the verifier |
| `onebig` | 1 round × 18 inner steps, same rollout and update budget | iteration and the gate vs one-shot RL |

* Yangquan, seeds 1-3: `yq_ofts_{fixed,nonrec,shuffled,onebig}_s{1,2,3}` (12 runs, one card each, source
  `rsi_src_v28`, plans from `scripts/baidu/mkplans_vla.py yq_spatial_main`). The checkpoint is already on the pool
  CFS (digest aef94c5a595fbdf9…, listed 2026-11-10 04:41Z).
* cavin, seed 0: `a8_spatmain_{fixed,nonrec,shuffled,onebig}_s0` (4 runs, one GPU each, code tree src5, generator
  `scripts/a800/mkoft_goal_main.py <order> 0 <arm> spatial`). This is the Goal layout (addenda 23, 25): pairing is
  within a seed, so a seed sits on one platform.
* Final of a run = per-episode mean of three evaluations of the retained policy (its own test + `--test-eval
  --replicates 2`). Initial reference per platform = per-episode mean of every in-run n0 test of this checkpoint and
  suite on that platform (Yangquan: the 12 runs here; cavin: the 4 runs here and `a8_spatmain_llm_harness_cap_s1`).
* Statistics as in the Goal read: seed-averaged per-episode paired bootstrap, 10,000 draws, 95% CI, the n0-halves
  noise check next to every verdict.

## Bars (the Goal bars, unchanged; read once when all 16 runs have `report.json` and both replicates)

* **R1-spatial: `fixed − reference` ≥ +5.0 points**, CI excludes 0, at least 2 of the 3 Yangquan seeds individually
  above 0 (Yangquan seeds 1-3). The +3 pilot level is shown next to it, as in the Goal read.
* **R2-spatial: `fixed − shuffled` ≥ +3.0**, CI excludes 0, seeds 0-3 (seed 0 paired within cavin); the 3-seed
  Yangquan statistic is reported alongside.
* **R3-spatial: `fixed − nonrec` ≥ +2.0**, CI excludes 0, same seeds.
* **R5-spatial: `fixed − onebig` ≥ +2.0**, CI excludes 0, same seeds; also against `onebig`'s single candidate
  whatever its gate (addendum 18 am. 1 form; a rejected candidate gets a `--test-eval --node r01c0` job first).
* Descriptive only, labelled as such: the same four differences pooled over Goal and Spatial (suite-averaged). Goal
  is already read, so a pooled number is not a registered claim and passes no bar.
* The reader is committed before any Spatial test file of these runs is opened. Negative readings are reported as
  such, next to the Goal table.

## Predictions, written before launch

* The Goal gate-level gain (+7.0 on its curve) became +1.7 on the sealed test. The Spatial curve gain (+7.6) and
  the one descriptive test (+2.6) point the same way: R1-spatial lands at +2 to +4, under the +5 bar; it may or may
  not exclude 0.
* `shuffled` ends at its start (as on Goal). R2-spatial is therefore R1 in size: about even odds at the +3 bar.
* R3-spatial at six rounds: positive, under +2 (on Goal the separation appeared only at 12 rounds).
* R5-spatial: a tie, as on Goal.
* If these fail as predicted, the paper reports two suites with the same pattern (small positive loop gain, bars
  missed) and the claims do not change. If R1 or R2 passes on Spatial, the paper states it for Spatial only.

## The Object curve of addendum 13

`a8_ofto_curve_grpo_s0` was registered in addendum 13 and never started: the checkpoint download failed, and on
2026-11-10 the directory on cavin is still empty. The download is retried; if the four shards arrive, the run starts
exactly as registered there (`scripts/a800/mkoft_suite.py <order> 0 object`, src3, one GPU, sealed, always-accept;
read D at rounds 5-6, bar +3; main arms on Object only through their own addendum). Nothing about it changes here.

## What is not changed

No registered read, bar or run changes. These 16 runs are read once, on their own, under the bars above.

## Operational notes (appended 2026-11-10 05:15Z; no design change)

* Times. The header says "~04:50Z"; the exact commit time of this addendum is 04:41:02Z (250b68b, pushed before any
  submission). The first job was submitted at 04:42:40Z. The reader `scripts/report/spatial_read.py`, the twelve
  Yangquan plans and the replicate-script change were committed at 04:42:48Z (f16c162), eight seconds after that first
  submission and hours before any run has a test; it was pushed at 04:48Z.
* Yangquan. `yq_ofts_fixed_s1` (job-x0wgqyvb472k, 04:42:40Z) went first as a canary. It reached the main run at
  04:57:10Z (environment setup took 861 s) and its GPU filled without an error, so the other eleven runs were
  submitted at 05:11:45-05:12:04Z: fixed s2 job-mueiz2a9wzdh, s3 job-knec13gc1jtx; nonrec s1-3 job-cyd12lbtsq8w,
  job-ithyujrhi4pn, job-2l28f81b9w33; shuffled s1-3 job-o4m19x87e23o, job-1z3anphyu3fu, job-morrsb5yx2wf; onebig s1-3
  job-zulxqty6nb2a, job-2t1obyt9uny9, job-srbg9gqisnfu. Source `rsi_src_v28`, one card each.
* A800 node. Queue orders 95-98: `a8_spatmain_fixed_s0` launched 04:42:57Z on GPU 0; nonrec, shuffled and onebig at
  04:43:57Z on GPUs 1, 2 and 4. The shuffled entry was queued a second time after the first ssh call timed out
  before writing anything; one entry exists.
* Checkpoints. A listing job on the Yangquan file system (job-66p7yw2ii31p, 04:39Z) showed the Spatial checkpoint
  complete (4 shards, digest aef94c5a595fbdf9). An earlier listing job (job-lsrw0vzb48ch) failed because it read a
  path that does not exist in script jobs; it touched nothing.
* Object curve. The checkpoint download on the A800 node was restarted at 04:42Z (`~/rsi/models/oft/dl_object.sh`,
  mirror, two workers, eight attempts); 3.0 GB of about 15 GB at 05:01Z. The run is queued once the four shards
  match the digest of the Yangquan copy (6653744e6ecc3a95).
