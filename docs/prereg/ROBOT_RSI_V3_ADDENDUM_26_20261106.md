# Prereg v3, addendum 26: a fourth seed for the self-repair study (addendum 24), on cavin

Committed 2026-11-06 ~05:10Z, before any run named here exists. State at commit time: the addendum-24 arms
`yq_oftgb_fixed_s1-3` and `yq_oftgb_full_s1-3` have `report.json` (their tests are sealed and unread);
`yq_oftgb_llm_harness_s1-3` are still running. No addendum-24 test has been opened.

## Why

Addendum 24 is the one setting in which a meta level can be told apart from RL: the loop starts from a procedure
that fails (BC at unit temperature on T = 1.6 samples, addendum 12) and the question is whether the loop with a
diagnosing meta level ends with a better policy than the same loop without one (S1, `llm_harness − fixed` ≥ +3) and
than blind search over the same knobs (S2). Three seeds give S1 little power against the ±1.5-point evaluation noise
documented in `docs/results/M2_V2_20261104.md`. cavin's eight A800 GPUs are idle now that its Goal runs have ended,
and seed 0 is the only unused value of the valid seed range 0-3 (addendum 21 am. 4a). Adding it mirrors addendum 23
(seed 0 for R2, R3 and R5).

## What is launched (cavin, source tree src10b)

`a8_oftgb_fixed_s0`, `a8_oftgb_full_s0`, `a8_oftgb_llm_harness_s0`: the addendum-24 arms with `engine.seed = 0`.
Program, proposer, candidates per round, rounds, inner steps, fresh paired gates and the official 500-episode test
are those of addendum 24 (`scripts/baidu/mkplans_bcstart.py`); the plan skeleton is cavin's Goal `fixed` seed-0
plan (addendum 25), so the platform fields (checkpoint path, GPUs, worker counts) are cavin's. The LLM arm calls
OpenRouter directly through cavin's outbound proxy (`bin/py_llmproxy.sh`, addendum 21 am. 2) instead of the
Yangquan relay; model, prompt, edit space and call cap are unchanged. src10b is the tree the cavin meta-v2 seed-0
runs used (addendum 21 am. 4a); for the harness space and the BC knobs it is the same code as rsi_src_v24.

## Read rule (unchanged bars)

* S1 and S2 are seed-averaged over seeds 0-3 (seed 0 paired within cavin, seeds 1-3 within Yangquan), bars
  unchanged (S1 ≥ +3, CI excludes 0; S2 reported with its CI). The 3-seed (Yangquan-only) statistic is reported
  alongside, as addendum 23 does for R2, R3 and R5.
* S3 (descriptive) adds the cavin seed-0 runs against `a8_goalmain_fixed_s0`.
* All addendum-24 tests stay sealed until all twelve runs have `report.json`; they are then read once.
* Fallback rounds (numeric search replacing a failed LLM call) are counted from the candidate author, as before.

## Operational note (2026-11-06 ~04:40Z): the registered replicate evaluations are launched; preliminary read disclosed

* The Goal read of `docs/results/GOAL_MAIN_READ_20261106.md` used each run's own single test (replicate 0) and its own
  n0 test. The registered final (prereg v3 "Test (sealed)"; VLA addendum 2) is the per-episode mean of three
  evaluations of the retained policy (own test + `run_libero --test-eval <run> --replicates 2`, same plan) against
  the per-episode mean of every in-run n0 test of the model and suite on that platform. That read is done once the
  replicates exist; `scripts/report/goal_read.py --mode final` implements it (mode `single` is the preliminary read).
  The preliminary numbers are reported as such and are not replaced.
* Launched: cavin queue jobs 71-83 (`<run>_rep`, 2 replicates, the run's own queue plan and source tree) for the 13
  cavin Goal runs; Yangquan jobs `<run>_rep` for the 17 Goal runs with a retained node other than n0 and for the six
  finished addendum-24 arms (`yq_oftgb_{fixed,full}_s1-3`, tests still unread), source tarball `rsi_src_v27.tgz`
  (the repository's `rsi/` package at de4528a; no change to any evaluation or training code since v24).
  `yq_oftg_onebig_s1` retained n0, so its final is the initial model by construction; its rejected candidate r01c0
  is evaluated three times for R5-ungated (`--node r01c0 --replicates 3`, addendum 18 am. 1).
* Nothing is re-trained; no test file is opened by these jobs.
* 06:34Z: two gate-only pilots for a possible second self-repair scenario were submitted to idle Yangquan cards
  (`yq_pilot_fail{1,2}_s{1,2}`, fixed proposer, 3 rounds, seeds 1-2; no test is read). Candidate failing recipes:
  fail1 = GRPO at lr 1e-4, temperature 2.0, clip [0.1, 0.5], z-scored advantages, token-level loss; fail2 = BC at
  rollout temperature 2.0 cloning up to 8 successes per scene. Only a recipe whose gate falls clearly below its
  start over three rounds would be registered (addendum 27) as scenario 2; otherwise nothing follows from them.
* 07:51Z: the same two pilot recipes also run on cavin (`a8_pilot_fail{1,2}_s1`, src10b, queue 91; gate-only, 3 rounds,
  seed 1) as a platform check, on GPUs freed by the finished replicate evaluations. No test is read.
* 07:45Z: the registered Goal read (`docs/results/GOAL_MAIN_FINAL_20261106.md`) met no bar; the preliminary R3 pass did
  not survive replicate averaging. This does not change anything registered for addenda 24/26.
* 14:40Z: the four `fail1`/`fail2` pilots (Yangquan seeds 1-2, cavin seed 1) show no degradation over the rounds seen so far
  (gates stay within noise of their start), so nothing follows from them. Two further gate-only pilots were queued on
  cavin's idle GPUs (`a8_pilot_fail{3,4}_s1`, src10b, queue 92; seed 1, 3 rounds, fixed proposer, no test read):
  fail3 = GRPO with large updates on low-diversity groups (temperature 1.0, band [0.3, 0.7], z-scored advantages,
  lr 1e-4, 800 steps x batch 16, clip [0.4, 0.5], token loss); fail4 = BC with many small-batch steps on few
  successes (temperature 1.0, per_case 8, lr 1e-4, 800 steps x batch 16, rollout-temperature likelihood, token
  loss). Every value lies inside the harness edit space, so a meta level could undo it. The registration rule is
  unchanged: only a recipe whose gate falls clearly below its start over three rounds becomes scenario 2
  (addendum 27). Extra seeds of scenario 1 are not possible: run seeds above 3 overflow the placement seed
  (addendum 21 am. 4a), so cavin's spare cards go to these pilots and, later, to the seed-0 replicate evaluations.
* 15:55Z (speed-up of the critical path; no change to any registered quantity): the cavin seed-0 arms run one
  GPU each at about 7.5 h per round, which puts the once-only read of this study beyond 2026-11-08. Each arm is
  therefore stopped at its next round boundary (after `round-NN.json` is written) and continued with
  `--resume` on the same `plan.json` with more rollout GPUs (`llm_harness` 3, `full` 2, `fixed` 2; training stays on one
  GPU). Only platform fields change (`vla.rollout_gpus`, which the resume check does not compare); rounds, seeds,
  gate sets, candidates per round and the test are unchanged. As addendum 25 documents for `onebig_s0`, the
  proposer's random stream is re-seeded from (seed, completed rounds) on resume, and `resume.json` records it.
  To free the cards, the exploratory `a8_pilot_fail3_s1` / `a8_pilot_fail4_s1` pilots were stopped 1.5 h in
  (no round scored, nothing read); `fail1_s1` finishes its third round. The Yangquan `fail2` pilots ended null
  (s1 60/64/62.5, s2 56.5/60/62.5 vs starts near 58-60).
* 16:05Z: the same round-boundary continuation is applied to the Yangquan LLM arms `yq_oftgb_llm_harness_s1-3`
  (one card each, about 9 h per round, 53 h job limit at 22:45Z). A probe job confirmed that a Yangquan job can hold
  several cards. Each arm is stopped after its next `round-NN.json` (or when its job ends at the limit, whichever
  comes first) and resumed on the same CFS run directory with three cards (`run_vla6.sh`: rollouts on all cards,
  training on card 0; `NGPU=3 scripts/baidu/resume_oftgb_llm.sh`). Plan, seeds, gate sets, relay slots and the test
  are unchanged; the resume re-seeds the proposer's random stream as before.
