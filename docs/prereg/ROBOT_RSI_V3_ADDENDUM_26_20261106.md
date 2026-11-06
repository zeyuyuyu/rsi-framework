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
