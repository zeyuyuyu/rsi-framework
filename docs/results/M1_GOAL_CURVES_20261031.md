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
| `bj_oftg_curve_bc` | BC on verified successes, lr 1e-5 | pooled 0.5475, 0.600, 0.6275, 0.600, 0.5875, **0.460** (final; r06 gate 0.44 / audit 0.48; **D -6.4**) | -4.0, +1.25, +4.0, +1.25, 0.0, -12.75 |
| `bj_oftg_curve_grpo_s2` | seed 2 replica (amendment 2, outside the rule) | n0 0.600 / 0.575 (identical to seed 0); gate r01 0.555, r02 0.580, r03 0.565, r04 0.645, r05 0.610 | gate -4.5, -2.0, -3.5, +4.5, +1.0 (seed 0: -1.0, +3.5, +5.5, +4.5, +6.5) |

Settings confirmed from the receipt: `loss_agg` episode, `ratio_mode` matched, lr 3e-5.

## BC collapse replicates on Beijing (2026-10-31, interim)

`bj_oftg_curve_bc` (seed 0, deterministic Beijing evaluation) follows the cavin seed-1 collapse about 1.5 rounds
later. Its exact sampled success held at 53-63% through round 4 (pooled r04 0.600). Then in round 5 the training
items fell 103 → 70 → 50 and the step-100 BC loss rose 0.687 → 1.127 → 1.536. On cavin this is the signature that
preceded the fall at r03-r04. It shows the same mechanism on two platforms, which fits the addendum-12 diagnosis:
unit-temperature NLL of T = 1.6 self-samples. GRPO, which scales the logits by the sampling temperature, shows no
such drift in any run (sampled success about 0.63 at bj seed 0's r05/r06).

**Addendum-11 rule for BC (read 2026-10-31): BC fails.** D is -6.4 on Beijing seed 0 and -48.1 on cavin seed 1,
and both runs collapse. The Beijing paired placement bootstrap (`nodebits3`, same 200 + 200 ids at every node) gives
D -6.37 [-11.37, -1.37], P(D <= 0) 0.994. r06 alone is -12.75 [-18.50, -6.75] (gate 51 down / 19 up, audit 46 / 27).
The early gains are not significant: r03 +4.00 [-0.75, +9.00], r02 and r04 +1.25. On Beijing, greedy success held through r05 and fell at r06, 1.5 rounds after the sampled
success did, the same order as on cavin. The rule's GRPO read is pending on cavin seed 1.

## cavin, seed 1 (A800, in progress)

| run | update | n0 S | S by round so far | change vs n0 |
|---|---|---|---|---|
| `a8_oftg_curve_bc_s1` | BC on verified successes, lr 1e-5 | 0.585 (gate 0.585, audit 0.585) | 0.5875, 0.5775, 0.560, **0.4475**, **0.1525**, **0.055** (final; r06 gate 0.07 / audit 0.04; **D -48.1**) | +0.25, -0.75, -2.5, -13.75, -43.25, -53.0 |
| `a8_oftg_curve_grpo_s1` | GRPO lr 3e-5, matched, episode loss | queued | | |
| `a8_oftg_curve_bct_s1` | BC with the NLL at the rollout temperature (addendum 12) | queued | | |

BC seed 1 collapsed in round 4: gate 0.400, audit 0.495. Sampled success fell from 53-66% (rounds 1-2) to 34%
at the last step of round 3, and to 20%, 11% and 1.5% over round 4. The BC loss rose 0.3 → 3.3. No rollout
errors. The diagnosis is that unit-temperature NLL of T = 1.6 self-samples flattens the policy on every step;
the fix and its pilot are in addendum 12.
Beijing BC seed 0 has not shown this through round 3: training items 96-102 per step, step-100 BC loss stepping
from ~0.32 (rounds 1-2) to ~0.40 (round 3) and not climbing within the round, r03 gate 0.640. Its exact sampled success stayed 53-63% through round 3, but the round-4 step-100 losses rose 0.343, 0.401, 0.523, and
the r04 gate fell to 0.575 (from 0.640). The exact r04 sampled success is 60.4 / 56.7 / 54.2%, and the r04 audit
rose to 0.625, so pooled r04 is 0.600 (+1.25). That reads as set noise, not collapse. The loss is rising while
success holds; r05 will show whether the in-round slide continues. Either the flattening rate depends on the run (seed, platform numerics), or something
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

## Beijing seed 2 GRPO, final (2026-10-31, outside the rule)

`bj_oftg_curve_grpo_s2` finished all six rounds. `nodebits4` (job-k4lvach7outw): same gate and audit ids as
seed 0 at every node, and the counts match the final accepted.jsonl.

| node | gate | audit | S |
|---|---|---|---|
| n0 | 120/200 | 115/200 | 0.5875 |
| r05c0 | 122/200 | 127/200 | 0.6225 |
| r06c0 | 117/200 | 125/200 | 0.6050 |

D = +2.63 points, paired 95% CI [-1.12, +6.50], P(D <= 0) = 0.094 (10k draws). The analytic paired SE gives 1.95,
so [-1.20, +6.45]. Flips against n0 are mostly on the audit half: r05 up 44 / down 30, r06 up 45 / down 38
(gate + audit). Seed 2 points the same way as seed 0 but is about a third of its size, and alone it does not
exclude 0. Seeds 0 and 2 resampled jointly (one draw of placements applied to both runs, 10k draws) give
+4.81 [+1.19, +8.56], P(D <= 0) = 0.004. This is a descriptive replication read, not the rule's statistic, and
seed 3 is still running.

## Beijing seed 3 GRPO, final, and the three Beijing seeds together (2026-10-31, outside the rule)

`bj_oftg_curve_grpo_s3` finished at 14:03Z (rc 0). `nodebits5` (job-fhm93dz7e2n9) used the same gate and audit
ids at every node as seeds 0 and 2, and its counts match the final accepted.jsonl.

| node | gate | audit | S |
|---|---|---|---|
| n0 | 120/200 | 115/200 | 0.5875 |
| r05c0 | 127/200 | 121/200 | 0.6200 |
| r06c0 | 124/200 | 123/200 | 0.6175 |

D = +3.12 points, paired 95% CI [-0.63, +6.88], P(D <= 0) = 0.057 (10k draws). The analytic paired SE is 1.93,
giving [-0.66, +6.91]. Flips against n0: r05 up 48 / down 35, r06 up 42 / down 30 (gate + audit).

All three Beijing seeds put D above 0: +7.00, +2.63 and +3.12. Only seed 0 excludes 0 alone. A joint bootstrap
over the three runs (one draw of the shared placements applied to every run and node, 10k draws) gives
**+4.25 [+0.83, +7.83], P(D <= 0) = 0.007**. That CI conditions on these three training runs: it resamples
placements, not training seeds. Treating the seed as the unit (n = 3, t with 2 df) gives mean +4.25, SD 2.39,
and [-1.70, +10.20], which does not exclude 0. So the defensible statement is: on fixed placements, all three
Beijing GRPO runs improve over n0, with a placement-level effect of about +4 points. Three seeds are too few to
bound the between-run spread. This is descriptive and outside the rule; the rule's read is bj seed 0 plus the
cavin seed-1 replica (r06 due about 16:30Z).

## cavin seed-1 GRPO replica: the addendum-11 rule read (2026-10-31 16:30Z)

`a8_oftg_curve_grpo_s1` finished all six rounds at 16:16Z (code 0). The per-placement greedy bits were read on
cavin with `pfs_nodebits.sh` (RUNROOT=~/rsi/runs2, over ssh). Every node's counts match accepted.jsonl. All nodes
use the same gate ids (c629d74a…) and audit ids (71d5ceb3…), which are the same sets as Beijing seeds 0, 2 and 3.

| node | gate | audit | S |
|---|---|---|---|
| n0 | 110/200 | 122/200 | 0.5800 |
| r05c0 | 123/200 | 122/200 | 0.6125 |
| r06c0 | 125/200 | 126/200 | 0.6275 |

**D = +4.00 points, paired 95% CI [+0.25, +7.87], P(D <= 0) = 0.020** (10k draws, gate and audit placements
resampled jointly as for seed 0). The analytic paired SE is 1.92, giving [+0.24, +7.76].

| split | D | 95% CI | P(D <= 0) |
|---|---|---|---|
| gate only | +7.00 | [+1.50, +12.75] | 0.007 |
| audit only | +1.00 | [-4.00, +6.00] | 0.37 |
| r05 only (pooled) | +3.25 | [-1.00, +7.50] | 0.073 |
| r06 only (pooled) | +4.75 | [+0.50, +9.00] | 0.018 |

Flips against n0: r05 gate 27 up / 14 down, audit 17 / 17; r06 gate 28 / 13, audit 20 / 16.

**Addendum-11 rule for GRPO: met.** The replica's D (+4.00) is at least -1.0, and the mean with Beijing seed 0
is (+7.00 + 4.00) / 2 = **+5.50**, which is at least +3. As registered, the rule specifies GRPO main arms. On the
identical placements, the two runs resampled jointly (one draw applied to both, 10k draws) give +5.50
[+2.56, +8.50], P(D <= 0) = 0.0001.

Caveats:
* On cavin the gain sits mostly on the gate half (+7.0), and the audit half alone is +1.0 and not significant. In
  an always-accept curve neither half picks anything, so the two are just independent 200-placement samples. The
  6-point gap between them is about 1.6 of its SE (about 3.8), which fits noise and is not evidence of selection.
* cavin's n0 gate (0.55) sits 5 points below Beijing's n0 on the same placements (0.60). A800-class evaluation is
  only near-deterministic, and n0 was evaluated once, so part of cavin's gate gain may come from a low n0 draw.
  The audit half has no such gap (cavin 0.61 vs Beijing 0.575).
* Across the four GRPO curves (Beijing 0/2/3, cavin 1), every D is positive: +7.00, +2.63, +3.12, +4.00.
* Per-set gate noise on 200 placements is about ±3.5 points (SE): r02c0 scored 0.660 on its own round-2 set and
  0.575 on the round-3 set. The low cavin n0 gate sits inside that range. Always quote the gate-only (+7.0) and
  audit-only (+1.0) halves together, never one of them alone.

What the rule result means:
1. The Goal main arms use GRPO as their operator. The running arms (fixed / full / onebig / llm / llm_harness /
   llm_harness_cap) already use the addendum-11 GRPO program, so nothing is relaunched or changed.
2. There are no BC main arms, because BC failed its read.
3. This is a statement about the object level, plain GRPO self-practice. It is **not** evidence for RSI and
   must not be worded as such. RSI is answered only by R4 / R5 / H-cap.

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
  noise for 18 steps. The addendum-11 reason ("from a mid-range start, more sampled groups contain both outcomes")
  is **not** supported by the round files. The mixed-group fraction is about the same on LIBERO-10: Beijing
  lr3e-5 episode 0.47-0.52, lr1e-4 0.43-0.55 per round. Goal's is 0.48-0.57. So LIBERO-10 does not lack mixed
  groups, and why it does not improve is open. Candidates: long horizons make the episode-level advantage
  noisier per token, and its mixed groups mostly hold one or two successes out of eight.
* The main-arm plan generator is ready (`mkplans_vla.py goal_main <grpo|bc> <bj|yq>`: five arms, seeds 1-3,
  fresh paired gates). It is not run until the rule fires, and the operator is fixed in its own addendum first.
