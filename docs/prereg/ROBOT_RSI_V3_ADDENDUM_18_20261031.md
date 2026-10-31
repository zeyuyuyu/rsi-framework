# Prereg v3, addendum 18: compute disclosure for meta arms, and resuming Yangquan runs that hit the job limit

Committed 2026-10-31 (~12:45Z). No main-arm run has finished, no main-arm test has been read, and no bar of
addenda 14-17 is changed here. What has been seen so far: round-1 gates of the fixed and `full` arms, and the
first LLM proposals of the `llm` / `llm_harness` arms (not yet scored).

## Why

The meta level edits the knobs inside the bounds of `domain.edit_space`, and three of them set how much work a round
does: `curriculum.cases` (40-400), `update.steps` (50-1500) and `solver.samples` (4-16). Nothing caps a proposal's
cost. The first LLM proposals on Yangquan (Goal s2, s3) doubled the scenes (64 → 128) and raised the steps
100 → 150; their first inner step trained on 552-600 items against about 290 for the incumbent. Addendum 14 says the
`llm` arm costs the same as `full` because both train two candidates per round. That holds for the candidate
count, not for the GPU time. A meta arm that wins by buying more rollouts would not show that the gain comes from the
loop rather than from more RL.

## Added analysis (disclosure; the bars stay as registered)

1. For every arm and seed, the report gives total GPU-seconds (rollout and train, from `backend-accounting.json`),
   the number of rollout episodes and the number of update steps, summed over all rounds and all candidates.
2. Each meta-arm bar (R4, R4-llm, R4-harness, R5, L10) is reported with its compute ratio: the arm's mean
   GPU-seconds over that of its comparison arm, same platform and seeds.
3. If a meta arm clears its bar with a ratio above 1.25, the result is labelled "not compute-matched". It is then
   not described as beating RL at equal compute. R5 (against `onebig`, which spends fixed's six-round budget in
   one round) is the equal-compute claim only when its ratio is at most 1.25.
4. The ratio is computed after the runs end and is not used to stop, select or rerun anything.

## Yangquan jobs that reach the 53 h limit

A Yangquan job stops its run after `RUN_TIMEOUT_S` = 190800 s. A round of the two-candidate arms takes about 10 h
when the proposal enlarges the program, so six rounds can exceed it. The run dir lives on the pool CFS
(`RSI_CFS_LINK=1`), so it survives the job. If a job ends this way before `report.json` exists, the same plan is
resubmitted with `RESUME_RUN=<run dir name>` (Engine `--resume`). The plan is unchanged, and so are the seeds and
the relay slots: the slot counter lives in the run dir. Finished rounds are kept. An unfinished round is rerun from
its parent. Every resume is listed in the results with its job ids. If a run cannot finish its six rounds before the
analysis date, its last finished round is reported as that run's final node, and the shortfall is stated.

## Amendment 1 (2026-10-31 ~21:10Z, before any main-arm test is read): R5 also against an ungated one-shot RL

`onebig` spends fixed's six-round budget in one round of 18 inner steps. Its candidate then faces the same gate as
every arm. On Yangquan s1 that candidate scored 0.59 on its fresh gate and was not accepted, so the arm's retained
node, and with it its test, is the starting checkpoint n0. SimpleVLA-RL-style one-shot RL keeps the trained policy
with no gate. Measuring R5 only against the gated `onebig` would let a gate rejection stand in for the RL baseline.

* **R5-ungated (sensitivity, registered now).** After the main arms finish, each `onebig` run's single trained
  candidate (`r01c0`) is scored on the official test (500 episodes, read once), whatever its gate. The tool is
  `run_libero --test-eval`, applied to the kept checkpoint. Engine checkpoints are never pruned.
* R5 is reported both ways: against the registered gated `onebig` and against the ungated candidate. The bar is
  unchanged: +2, CI excluding 0. The RSI-beats-one-shot-RL claim is made only if both reads clear the bar. If they
  disagree, both are stated.
* Compute ratios (this addendum) are computed for both.

## Amendment 2 (2026-10-31 ~22:20Z): an early test read, and a design freeze from here on

The registered rule is that the official test (500 episodes) is read once, after all main arms finish. At about
22:15Z the working session read the finished runs `a8_goalmain_fixed_s1` and `a8_goalmain_fixed_s2` early. Both
runs had completed with code 0.

The numbers:
* s1: n0 0.590, final 0.616, D +2.60, CI [-0.80, +6.00].
* s2: n0 0.576, final 0.590, D +1.40, CI [-2.0, +4.6].

These numbers are now known while the other arms are still running. To keep that knowledge from shaping the
experiment:

* **Design freeze from 22:20Z.** No new arm, bar, analysis, seed or program change is registered from here on.
  This covers addenda 14-20 and their amendments as they now stand. The only changes allowed are operational:
  rerunning a crash unchanged, resuming after a job time limit (this addendum), and the reads already registered,
  such as R5-ungated, H-cap and fixed_t12.
* **No more early reads.** No other test file is opened until every main arm has its `report.json`. The two early
  values above stay as they are and are not reread.
* **Disclosure.** The final write-up states this early read and its time.
