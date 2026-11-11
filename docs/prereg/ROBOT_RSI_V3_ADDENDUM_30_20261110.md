# Prereg v3, addendum 30: a sealed fresh-scene test for every robot study, and the 12-round horizon on LIBERO-Spatial

Committed 2026-11-10 before any evaluation or run named here exists. The fresh-scene test set defined below has never
been generated or scored. State of the other studies at commit time: addendum 28 (Spatial main) and addendum 29
(Spatial self-repair, meta level v3) are running, none of their runs has finished, and the only records seen are
gate-level round files of the five A800 seed-0 runs through round 4 (`docs/STATUS_TODO_20261110.md`).

## Why

**The official test is the wrong ruler for half of what the loop does.** The loop practises, gates and audits on
freshly sampled object placements. The registered endpoint so far is the official benchmark: 50 fixed initial states
per task. Two things are on record about that endpoint. (1) It is not a neutral sample of the scenes the policy is
trained for: on LIBERO-10 the same one-demonstration start scores 14.6% on the official states and 20.0% on fresh
placements, and a published RL checkpoint drops from 87.4% to 76.0% when the states are fresh
(`docs/results/TRAIN_ON_TEST_INFLATION_20261030.md`). (2) The only fresh-scene measure the runs carry is the audit
set, 200 episodes, which nobody decides on; one audit reading has a standard deviation of about 3 points, too coarse
to carry a claim. The audit records point the same way in every study: gated GRPO runs end about +2 to +4 above
their start on Goal audits and +5.5 to +8.5 on the two finished Spatial runs, the shuffled-label control at 0.0,
the 12-round non-recursive control at −5.8 (computed 2026-11-10 from `accepted_chain` in the reports; descriptive,
never registered). A claim about self-improvement on unseen scenes needs a fresh-scene test with enough episodes,
sealed and registered before it is scored. This addendum adds one. **It replaces nothing**: every official-test bar
stays as registered and is reported next to the fresh-scene result, whatever either shows.

**The recursion result has one suite.** Recursion against a frozen generator separates at 12 rounds on Goal (R3-long
+7.84 [+5.22, +10.49], addendum 27) and not at 6 (R3 +1.72). The Spatial main study runs 6 rounds. On the A800
seed-0 Spatial run the gated loop has been accepted in four of four rounds (mean gate change +1.1 points per round),
so the horizon question is open on Spatial in both directions: does the gain keep growing, and does the frozen
generator fall behind.

## Part A: the sealed fresh-scene test

* **Set.** `LiberoDomain.fresh_test(100)`: 100 sampled placements per task, 1000 per suite, placement seeds
  970,500,000 + 1000 × task + k. No training, gate, fresh-gate or audit seed can take these values (training seeds
  have an offset below 130,000 inside their 1,000,000 block; a unit test checks the ranges). The set is the same
  for every run and both platforms.
* **Evaluation.** `rsi.run_libero --fresh-eval <run dir>` scores the run's retained policy once, greedy, as every
  other evaluation (1000 episodes, about one card-hour). The initial policy is scored four times per suite and
  platform (`--fresh-eval none --node n0`); the reference is the per-episode mean of those. The official test is
  not touched by this mode.
* **Runs covered.** Spatial main (addendum 28, 16 runs), Spatial self-repair (addendum 29, 15 runs), Spatial 12
  rounds (part B), Goal main (`yq_oftg_{fixed,nonrec,shuffled,onebig}_s1-3`, `a8_goalmain_*_s0`, 16 runs) and Goal
  12 rounds (addendum 27, 9 runs). The Goal runs are finished and read on the official test; their retained
  adapters are on the pool file system and the A800 node.
* **Statistics.** As for the official test: paired per episode within a platform, seed-averaged, paired bootstrap,
  10,000 draws, 95% CI; a noise figure from two halves of the reference evaluations. Reader
  `scripts/report/fresh_read.py`, committed with this addendum; one read per block, when every run of the block
  has its fresh evaluation.

| block | claim | comparison | bar |
|---|---|---|---|
| Spatial main | F1-spatial | fixed − initial | ≥ +3, CI > 0 |
| | F2-spatial | fixed − shuffled | ≥ +3, CI > 0 |
| | F3-spatial | fixed − nonrec | ≥ +2, CI > 0 |
| | F5-spatial | fixed − onebig | ≥ +2, CI > 0 |
| Goal main | F1/F2/F3/F5-goal | the same four | the same bars |
| Spatial self-repair | FS1 | meta3 − fixed (BC start) | ≥ +3, CI > 0 |
| | FS2 | meta3 − full | reported with CI |
| Spatial / Goal 12 rounds | FL1 | fixed12 − initial | ≥ +5, CI > 0 |
| | FL3 | fixed12 − nonrec12 | ≥ +2, CI > 0 |
| | FL5 | fixed12 − onebig12 (where onebig12 exists) | ≥ +2, CI > 0 |

The bars are the registered ones of the corresponding official-test claims, except F1, which takes the "+3 shown"
level of R1 as its bar (R1's own bar of +5 is reported as well). The Goal blocks are registered here after their
audit records were seen (above), so they are a confirmation on a new sample, not a first look; the Spatial blocks
are registered before any Spatial run has finished.

## Part B: LIBERO-Spatial, 12 rounds (Yangquan, seeds 1-3, source rsi_src_v30 = this commit's `rsi/`, tarball sha256 96f247d2e77091ea...)

Addendum 27's design with the suite changed: the Spatial main program (GRPO, lr 3e-5, matched ratio, episode loss,
T 1.6, 64 scenes per inner step, 100 steps × batch 64), fresh paired gates, `heldout_per_task` 40,
`test_inits_per_task` 50.

| runs | engine | isolates |
|---|---|---|
| `yq_ofts_fixed12_s{1,2,3}` | 12 rounds × 3 inner steps, recursive | the gated loop at twice the horizon |
| `yq_ofts_nonrec12_s{1,2,3}` | the same, `recursive: false` | recursion |
| `yq_ofts_onebig12_s{1,2,3}` | 1 round × 36 inner steps | iteration and the gate against one-shot RL |

`fixed12` is submitted first, `nonrec12` as soon as three cards are free. `onebig12` is submitted only if three
cards are free by 2026-11-11 16:00Z; if not, R5-long-spatial and FL5-spatial are not tested and the paper says so.

Official-test bars, as in addendum 27 (final = per-episode mean of three evaluations; pooled n0 reference of the
Yangquan Spatial runs): **R3-long-spatial** fixed12 − nonrec12 ≥ +2, CI > 0 (primary); **R1-long-spatial**
fixed12 − reference ≥ +5, CI > 0, at least 2 of 3 seeds > 0; **R5-long-spatial** fixed12 − onebig12 ≥ +2, CI > 0, if
run; fixed12 against the 6-round `fixed` of the same seeds, descriptive. Reader:
`scripts/report/spatial_long12_read.py`, committed with this addendum. One read when the runs submitted have
`report.json` and both replicates.

## Predictions, written before launch

* **F1-spatial** +4 to +7, passes (about 70%). **F2-spatial** +3 to +6 (55%). **F3-spatial** +1 to +4 at six
  rounds (45%). **F5-spatial** a tie: one-shot RL at equal compute has matched the loop everywhere so far.
* **Goal on the fresh test**: F1 between +1.5 and +3, CI above 0, under the +3 bar; F2 about the same size; F3 small;
  F5 a tie. If Goal's F1 is under +1, the audit figures above were selection or noise and the paper says so.
* **FS1** (meta3 − gate-only from the BC start) +3 to +7, passes (60%).
* **12 rounds on Spatial**: fixed12 keeps climbing, FL1 +6 to +10 and R1-long-spatial +3 to +6 (even odds on its +5
  bar); nonrec12 stops or degrades after about four rounds, so R3-long-spatial and FL3 pass (65%). onebig12, if
  run, ties fixed12.
* **Goal 12 rounds on the fresh test**: FL3 passes (the audit already had fixed12 +2.7 and nonrec12 −5.8); FL1
  under +5; FL5 a tie or onebig12 ahead (audit +6.5 against +2.7).
* If the fresh-scene results are no larger than the official ones, the conclusion "small loop gains under these
  budgets" stands on both rulers and the paper states that the fresh-scene ruler did not change it.

## Scheduling (no design change to addendum 29)

Cards are the constraint: about fifteen at once. So that the runs behind addendum 29's primary bar and the
evaluations that close addendum 28 start first, six addendum-29 jobs that are still waiting in the queue and have
never started (`yq_oftsb_full_s1-3`, `yq_ofts_meta3_s1-3`) are stopped and resubmitted later under the same names
and plans. Order of use as cards free: addendum 29 `fixed` and `meta3` (BC start); `yq_ofts_fixed12`; replicates
and fresh evaluations of the Spatial main runs; `yq_ofts_nonrec12`; `yq_oftsb_full`; `yq_ofts_meta3`;
`yq_ofts_onebig12`; fresh evaluations of the Goal runs in gaps.

## What is not changed

Every registered read, bar and run stands. The official test remains the endpoint of prereg v3 and of addenda 27-29;
the fresh-scene test is an additional registered endpoint, reported beside it in every table.

## Operational notes (appended 2026-11-10 17:15Z; no design change)

* Registered as 7aa7764 at 17:06:51Z, pushed 17:06:55Z, before the first action below.
* Stopped while still waiting in the queue (status Created, never started), to be resubmitted under the same names
  and plans: `yq_oftsb_full_s1-3` (job-2ip8kewtmsqc, job-mt68wtwe23ag, job-gr8sajq84v2y) and `yq_ofts_meta3_s1-3`
  (job-mq6tvlzyelsc, job-e6pnli6w5441, job-4wftsmvpoygl). Their relay slots are unused and are kept.
* Submitted at 17:07:36-17:07:40Z, one card each, source `rsi_src_v30`: `yq_ofts_fixed12_s1` job-5d0iaxdoo28y,
  `yq_ofts_fixed12_s2` job-wumqqydmldl6, `yq_ofts_fixed12_s3` job-l3do0ww1n6fw. They wait for cards with the four
  addendum-29 runs still queued (`yq_oftsb_fixed_s2-3`, `yq_oftsb_meta3_s2-3`).
* `scripts/baidu/close_yq.sh` submits, for every finished Yangquan run of addenda 28-30, the two replicate test
  evaluations and the fresh-scene evaluation that are still missing (at most six jobs per call).
* A bounded-slack gate (accept a child that is within one noise standard deviation of its lineage's best) was
  considered and not registered: on the finished Goal runs of the A800 node the strict gate refused 15 of 24 rounds,
  11 of them for dips within 3 points, but the mean gate change of a round there is −0.5 ± 0.6, so there is no gain
  for a looser gate to keep; on the running Spatial seed-0 run the strict gate has accepted four of four rounds.

## Amendment 1 (2026-11-10 19:35Z, before any 12-round Spatial run has started): a seed-0 block on the A800 node

The A800 node's cards free up tonight as the addendum-28 seed-0 runs end, and the instruction for this stage is to
keep every card busy. Two runs are added there, two cards each (rollouts on both, training on the first), source
`src12` (the repository's `rsi/` at this addendum): `a8_spatmain_fixed12_s0` and `a8_spatmain_nonrec12_s0`
(`scripts/a800/mkoft_spatial_long12.py`). As with addendum 23/25, pairing is within a platform; **the registered
statistics stay the Yangquan three-seed ones (R3-long-spatial, R1-long-spatial, FL1, FL3)**, and the four-seed
statistic with seed 0 is reported alongside. Their replicates and fresh-scene evaluations run on the node.

Queue record: the three `yq_ofts_fixed12` jobs submitted at 17:07Z were stopped at 19:20Z while still waiting
(never started), together with `yq_oftsb_fixed_s2-3` and `yq_oftsb_meta3_s2-3` of addendum 29, so that the first
cards freed tonight go to evaluations (Goal 12-round fresh-scene evaluations, submitted 19:21Z:
`yq_oftg_{fixed12,nonrec12,onebig12}_s1-3_fresh`, `yq_fresh_n0_goal_1-4`; then the replicates and fresh-scene
evaluations of the Spatial main runs). The stopped runs are resubmitted under the same names and plans right after.
* (19:30Z) Amendment 1 was committed as c4b9c5b at 19:26:02Z (its heading says 19:35Z; the commit time is the
  record). Queued on the A800 node at 19:26Z, not yet started: `a8_spatmain_fixed12_s0` (order 89, two cards) and
  `a8_spatmain_nonrec12_s0` (order 90, two cards). A watcher on the node (`close_runs_1111b.sh`) queues the two
  replicate test evaluations and the fresh-scene evaluation of every seed-0 run when its `report.json` appears, four
  fresh-scene evaluations of the initial Spatial policy, and the fresh-scene evaluations of the four finished Goal
  seed-0 runs with four of the initial Goal policy.
- 2026-11-11 02:24Z: four of the twelve Goal main fresh-scene evaluations (`yq_oftg_fixed_s1-3`, `yq_oftg_nonrec_s1`)
  submitted by hand onto four idle Yangquan cards, ahead of the conductor (jobs `job-n1eptjods790`,
  `job-5izbsljvpe70`, `job-vr8bo8ym7d1u`, `job-cd8a8pjvkljp`). `submit_fresh_yq.sh` now skips an evaluation that
  already has a job, so the conductor's later calls for these four do nothing. On the A800 node the four fresh-scene
  evaluations of the initial Spatial policy finished (02:18Z) and those of the initial Goal policy started. Nothing
  has been read.
