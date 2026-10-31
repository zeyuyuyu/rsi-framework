# M1 on LIBERO-Goal (OFT 1-traj SFT): addendum-11 pilot curves, interim (2026-10-31)

Status: **Beijing seed 0 is complete and read once at rounds 5-6 (below). The addendum-11 rule averages it with
the cavin seed-1 replica (running), so the rule has not fired yet.** One seed is not a conclusion.

Pilots are sealed, so no test was read. S = (gate + audit) / 2, 400 sampled placements, always-accept curves
(no selection), Beijing evaluation (deterministic: all variance below comes from placement sampling).

## Background, in brief

* **Model.** OpenVLA-OFT (7B vision-language-action model). It reads a camera image and an instruction ("put
  the bowl on the plate") and outputs robot-arm actions. The start is SimpleVLA-RL's checkpoint fine-tuned on
  one human demonstration per task, so it is weak: about 59% on LIBERO-Goal and 19% on LIBERO-10.
* **Benchmark.** LIBERO, a simulated tabletop arm. LIBERO-Goal has 10 goals in one scene; LIBERO-10 has 10
  long, multi-step tasks. Each episode starts from a random object placement and succeeds if the goal is reached
  within the step limit.
* **What the framework does each round.** The current policy practices on fresh random placements (8 tries
  each). The simulator reports only success or failure, so there are no human demonstrations, labels or reward
  shaping. The framework turns those outcomes into an update (here GRPO, a policy-gradient RL method), trains
  the next policy from the current one, and repeats. One round = 3 such updates; 6 rounds per run. The official
  test states stay sealed.

## What "improvement" means here

The change, in percentage points, in task success rate on 400 placements never used for training. Decoding is
greedy, and there are two halves:

* **gate** (200): the framework may see this half;
* **audit** (200): never shown to the framework or used for any decision, so it guards against the framework
  grading itself.

The measure, fixed before the run, is D = mean success over rounds 5-6 minus the starting model's, and the bar
is +3. Seed 0's result: start 58.75% (235/400) → 65.5% (r05) and 66.0% (r06), so **D = +7.0 points**. That is
about 28 more successful episodes out of 400, with 95% CI [+2.9, +11.3]. The audit half alone gives +6.25,
CI [+0.5, +12.3].

## Is the gain due to the RSI design? (what this does and does not show)

* **Shown:** a policy improves on unseen placements by practising in the framework's loop, with sim success as
  its only feedback: no new human data, no test-state training, no selection of lucky checkpoints (every round
  is accepted).
* **Not yet shown:** that the *recursive self-improvement* parts are what cause it. This run is the `fixed`
  configuration (a fixed recipe, each round building on the last). So far its result is equally consistent
  with "repeated on-policy RL works from a mid-range start". The prereg-v3 main arms separate these, each
  against `fixed` with the same budget:

| comparison | question it answers | prereg bar |
|---|---|---|
| `fixed` vs `shuffled` (success labels permuted) | does the gain need the real verifier signal? | +3, CI excludes 0 |
| `fixed` vs `nonrec` (every round practises with the initial policy) | does building on the improved policy matter? | +2 |
| `full` vs `fixed` (the meta level proposes the recipe) | does self-modifying the recipe add anything? | +2 |
| best of `fixed`/`full` vs `onebig` (the same total budget as one round) | does iterating beat one-shot RL, SimpleVLA-RL-style? | +2 |

  These arms start only when the addendum-11 rule fires (the seed-0 and cavin seed-1 mean D >= +3).
* **Framework-specific design changes inside this run.** These are the matched-ratio old log-probs (addendum 6)
  and the episode-balanced loss (addendum 7), both introduced after earlier null results. Their contribution on
  LIBERO-Goal has not been ablated.

## Beijing, seed 0

n0: gate 0.600, audit 0.575, S 0.5875 (both runs share it).

| run | update | S by round 1 → 3 | change vs n0 |
|---|---|---|---|
| `bj_oftg_curve_grpo` | GRPO lr 3e-5, matched ratio, episode loss | 0.6075, 0.6175, 0.650, 0.6325, 0.655, 0.660 (final) | +2.0, +3.0, +6.25, +4.5, +6.75, +7.25 |
| `bj_oftg_curve_bc` | BC on verified successes, lr 1e-5 | gate r01 0.570, r02 0.580, r03 0.640 (audit read at the end) | gate -3.0, -2.0, +4.0 |
| `bj_oftg_curve_grpo_s2` | seed 2 replica (amendment 2, outside the rule) | n0 0.600 / 0.575 (identical to seed 0); gate r01 0.555, r02 0.580 | gate -4.5, -2.0 (seed 0: -1.0, +3.5) |

Settings confirmed from the receipt: `loss_agg` episode, `ratio_mode` matched, lr 3e-5.

## cavin, seed 1 (A800, in progress)

| run | update | n0 S | S by round so far | change vs n0 |
|---|---|---|---|---|
| `a8_oftg_curve_bc_s1` | BC on verified successes, lr 1e-5 | 0.585 (gate 0.585, audit 0.585) | 0.5875, 0.5775, 0.560, **0.4475** | +0.25, -0.75, -2.5, **-13.75** |
| `a8_oftg_curve_grpo_s1` | GRPO lr 3e-5, matched, episode loss | queued | | |
| `a8_oftg_curve_bct_s1` | BC with the NLL at the rollout temperature (addendum 12) | queued | | |

BC seed 1 collapsed in round 4: gate 0.400, audit 0.495. Sampled success fell from 53-66% (rounds 1-2) to 34%
at the last step of round 3, and to 20%, 11% and 1.5% over round 4. The BC loss rose 0.3 → 3.3. No rollout
errors. The diagnosis is that unit-temperature NLL of T = 1.6 self-samples flattens the policy on every step;
the fix and its pilot are in addendum 12.
Beijing BC seed 0 has not shown this through round 3: training items 96-102 per step, step-100 BC loss stepping
from ~0.32 (rounds 1-2) to ~0.40 (round 3) and not climbing within the round, r03 gate 0.640. At r04 step 0 its loss fell back to 0.34
with 97 items, so the drift is absent there so far. Either the flattening rate depends on the run (seed, platform numerics), or something
specific to the cavin run contributes. The temperature-matched pilot is the direct test.

## Beijing seed 0 GRPO: the addendum-11 read at rounds 5-6 (2026-10-31, one read)

Second session, `nodebits2` (job-0w0nr2d1ecjp). The counts match the final log's accepted.jsonl exactly, and all
nodes share the same gate ids (c629d74a…) and audit ids (71d5ceb3…).

| node | gate | audit | S |
|---|---|---|---|
| n0 | 120/200 | 115/200 | 0.5875 |
| r05c0 | 133/200 | 129/200 | 0.6550 |
| r06c0 | 138/200 | 126/200 | 0.6600 |

**D = +7.00 points, paired 95% CI [+2.88, +11.25], P(D <= 0) = 0.0006.** The bootstrap uses 10k draws, and each
draw resamples the gate and audit placements once and applies them to n0, r05 and r06.

| split | D | 95% CI | P(D <= 0) |
|---|---|---|---|
| gate only | +7.75 | [+1.75, +13.75] | 0.0066 |
| audit only (never used for any decision) | +6.25 | [+0.50, +12.25] | 0.017 |

Flips against n0: r05 up 64 / down 37, r06 up 58 / down 29 (gate + audit). An analytic check from these counts
(this session) gives paired SEs of 2.49 (r05) and 2.30 (r06) points, consistent with the bootstrap CI.

Reading: on its own pre-registered measure, this run clears the +3 bar, and its CI excludes 0. So does its
never-selected audit half alone. This is an always-accept curve, so no selection inflates it, and the Baidu
evaluation is deterministic. The rule averages it with the cavin seed-1 replica (started 2026-10-31 01:29Z). If
that run's D is at least -1.0, the mean reaches +3 and the rule specifies GRPO main arms. Seeds 2 and 3 (Beijing,
outside the rule) are running.

## Paired check on identical placements (second session, 2026-10-31)

Reader `scripts/baidu/pfs_nodebits.sh` (job `zw-rsi-script-nodebits1`) takes per-placement greedy outcomes from
the run's call directories, with the node identified from `spec.adapter`. Its counts reproduce the summaries exactly:
n0 120/200 gate, 115/200 audit; r03c0 131 and 129. The placement-id hashes are identical across nodes
(gate c629d74a…, audit 71d5ceb3…). Bootstrap: 10k resamples of placements. Sign test: exact, on discordant
pairs.

| comparison | episodes | change | 95% CI | up / down | p |
|---|---|---|---|---|---|
| n0 → r01c0 | 400 | +2.00 | [-2.0, +6.0] | 38 / 30 | 0.40 |
| n0 → r02c0 | 400 | +3.00 | [-1.2, +7.2] | 45 / 33 | 0.21 |
| n0 → r03c0 | 400 | **+6.25** | [+1.8, +10.8] | 56 / 31 | 0.010 |
| n0 → r03c0, gate only | 200 | +5.50 | [-1.5, +12.5] | 29 / 18 | 0.14 |
| n0 → r03c0, audit only | 200 | +7.00 | [+1.0, +13.0] | 27 / 13 | 0.038 |

## Reading so far

* This is the first M1 node whose gain clears placement noise on identical placements. The audit half carries
  it, and the audit is never used for any decision in the run.
* Three rounds have been looked at, so a rough multiple-look correction puts the round-3 p near 0.03. The
  rule's rounds 5-6 are still ahead.
* Seed replicas share the gate and audit placements. The seed changes only the training placements and the
  sampling: `bj_oftg_curve_grpo_s2` (addendum 11 amendment 2, outside the rule) reproduced n0 exactly, gate 0.600 and
  audit 0.575. So a mean over seeds removes training noise but not placement-sampling noise. Any cross-seed CI must
  resample placements jointly across the seeds.
* One seed with results so far. Seed 2 is running on Beijing, and the cavin seed-1 GRPO replica
  (`a8_oftg_curve_grpo_s1`) is queued for the next free GPU.
* Contrast with LIBERO-10 (`M1_RECIPE_CURVES_20261031.md`), where the same recipe from a 19% start stays within
  noise for 18 steps. This fits the addendum-11 reason: from a mid-range start, more sampled groups contain both
  outcomes and carry a GRPO signal.
* The main-arm plan generator is ready (`mkplans_vla.py goal_main <grpo|bc> <bj|yq>`: five arms, seeds 1-3,
  fresh paired gates). It is not run until the rule fires, and the operator is fixed in its own addendum first.
