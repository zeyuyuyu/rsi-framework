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

## Done (17:41Z)

* Stopped on Yangquan (all in round 1, unscored): `yq_oftg_fixed_s0` job-34uta55xtrp3 17:40:45Z,
  `yq_oftg_nonrec_s0` job-2pzb8q3j0yin 17:40:49Z, `yq_oftg_shuffled_s0` job-qm65vcxhfsb6 17:40:52Z,
  `yq_oftg_onebig_s0` job-4b9x3p1wmglh 17:40:55Z, `yq_oftgb_fixed_s3` job-dqg3chkgttmo 17:41:01Z.
* `yq_oftgb_fixed_s3` resumed as job-ljwhdzou3x5l (`--resume`, rsi_src_v24).
* cavin queue: `a8_goalmain_{fixed,nonrec,shuffled,onebig}_s0` (jobs 64-67, src5), each differing from
  `a8_goalmain_fixed_s1` only in `engine.seed` and the arm's engine field.

## Operational note (2026-11-05 ~03:40Z): `a8_goalmain_onebig_s0` rollout worker crash and resume

* 03:32Z: the run failed at inner step 12 of its single 18-step round (work step 28, a rollout): one of three
  rollout workers died in `mujoco.MjrContext` with `Offscreen framebuffer is not complete, error 0x8cdd` (EGL
  offscreen renderer on GPU 6). No code or data error; at the same time other users' processes appeared on cavin
  GPUs 0, 6 and 7 (25-65 GB each). The backend's retry wrapper did not recover it; the engine wrote `failure.json`.
* 03:36Z: resumed with `--resume` on the same plan file (`queue/plans/a8_goalmain_onebig_s0.json`, GPU 6) and
  source tree (src5), launched by hand because the queue runner only starts jobs on GPUs with under 2 GB in use and
  every GPU now carries another user's job; the GPU is recorded in `queue/reservations.json` (pid 370274). Per the
  engine's resume rule the unfinished round 1 (checkpoints `ckpt-r01c0-i0..i11`, its attempts/cases files and
  `failure.json`) is set aside in `resume-01/` and round 1 is rerun from its start with the same step seeds. Nothing
  about the arm, recipe or bars changes.
* Effect on timing: round 1 now ends about 13:40Z and the test about 16:00Z on 2026-11-05, so the Goal read-once
  (R1-R5, seeds 0-3) moves from ~14:00Z to ~16:00Z.
* 03:43Z update: the resumed `onebig_s0` never got GPU 6: another user's job (25.7 GB, 100% util) holds GPUs 1, 2,
  4 and 6, and the backend's admission rule (`admit_max_used_mib` 8000, wait up to 4 h, then refuse) kept it waiting.
  It was stopped before doing any work and resumed once more on the then-free GPU 0 (`queue/plans` GPU fields
  rewritten to [0]; these fields are not part of the resume-checked `plan.json`; pid 390917, reservation recorded).
  It is rolling out on GPU 0 since 03:43Z. `fixed_s0` (GPU 1), `nonrec_s0` (GPU 2) and `a8_m2_pre_llm_s0` (GPU 4)
  are likewise waiting in admission at the start of a rollout phase (fixed/nonrec: round 4 after one inner step;
  llm_s0: round 6 candidate 1); they will proceed on their own when the GPUs clear, and fail with
  `gpu_admission_refused` after 4 h otherwise. A move of `nonrec_s0` to GPU 7 at 03:47Z was aborted by the move
  script's guard because GPU 7 had just been taken. If the GPUs are still held at ~05:15Z, fixed_s0 and nonrec_s0
  will be stopped and resumed with admission relaxed to share the GPU (`admit_max_used_mib` 30000,
  `sample_procs_per_gpu` 2: rollouts 1.5x slower, same episodes and seeds); llm_s0 by 06:45Z. Each such restart
  reruns the unfinished round from its start, as the engine's resume rule prescribes, and is listed here.
* 04:15Z: the other user's jobs ended between 03:50Z and 04:10Z; `fixed_s0`, `nonrec_s0` and `a8_m2_pre_llm_s0` were
  admitted on their own GPUs and are rolling out (three workers each). No further restart was needed; the
  contingency above was not used. Lost time: about 40 min of waiting per run, plus the onebig_s0 round-1 rerun.
