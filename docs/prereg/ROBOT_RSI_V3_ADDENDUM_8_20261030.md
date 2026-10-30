# Prereg v3, addendum 8 (M1): the update-recipe sweep and the main arms move to the Yangquan A800 pool

Committed 2026-10-30 (~05:30Z) before any pilot-7 round result and before any Yangquan run. No v3 run has read
a test result.

## Why

Sixteen A800-80GB cards are free in the Baidu Yangquan pool (`aihc-rd-yangquan`, queue `yangquan-research`).
The Beijing pool gives us 3 concurrent jobs. On Beijing the 15 M1 main arms would take about 5 days. Yangquan
can run them all at once, in about a day. Addendum 7's recipe decision rests on one seed per curve, and with a
±2.7-point gate noise one seed is weak. On Yangquan every recipe can run on two seeds.

## Platform

Yangquan is A800 (sm_80) with the Baidu image's stack and no shared PFS. Its numbers are compared only with
other Yangquan numbers. Before any sweep result is used, a 500-episode n0 evaluation on Yangquan is compared
with cavin and Beijing and reported. All M1 main arms then run on Yangquan, so the one-platform-per-comparison
rule of prereg v3 holds. M1 on Beijing (pilots 5 and 7) becomes development evidence.

## Sweep (sealed, Yangquan, 1 card each)

Always-accept learning curves, otherwise as `bj_oft3_pilot5_curve`: 6 rounds x 3 inner on-policy steps of 64
placements, 100 steps of batch 64, gate and audit 200 + 200, matched ratio everywhere.

| | token loss | episode-balanced loss |
|---|---|---|
| lr 1e-5 | `yq_oft3_curve_lr1e5_tok_s{1,2}` | `yq_oft3_curve_lr1e5_ep_s{1,2}` |
| lr 3e-5 | `yq_oft3_curve_lr3e5_tok_s{1,2}` | `yq_oft3_curve_lr3e5_ep_s{1,2}` |
| lr 1e-4 | `yq_oft3_curve_lr1e4_tok_s{1,2}` | `yq_oft3_curve_lr1e4_ep_s{1,2}` |

That is 12 runs. Validity: each run's first receipt must show a step-1 out-of-band share of 0 and the declared
`loss_agg`.

## Decision rule for the M1 main-arm update (replaces addendum 7's rule), fixed now

For a run, S(round) = (gate + audit) / 2, and D = mean of S over rounds 5 and 6, minus S at that run's own n0.
For each of the six recipes, D is averaged over its two seeds.

1. The main arms use the recipe with the highest mean D, provided that mean D is at least +3 points. If two
   recipes are within 1 point, the one with the smaller lr wins, and token loss wins over episode loss: the
   smaller change from the default wins.
2. If no recipe reaches +3, the M1 main arms are not launched. The negative result is reported with the
   diagnostics, and the next addendum says what changes.
3. The Beijing curves (pilot5_curve, pilot7_lr3e5, pilot7_lr3e5_ep) and the cavin seed-1 replicas are reported
   next to the sweep. Agreement or disagreement of their ordering is stated. They do not enter the rule.

## Main arms (after the rule picks a recipe)

The five arms of prereg v3 (fixed, full, nonrec, shuffled, onebig) on seeds 1-3 run on Yangquan, one card each,
with the chosen recipe in 6 rounds x 3 inner steps. `onebig` gets one round with all 18 inner steps. The
acceptance test of the gated arms is changed before launch. Every accepted gate gain so far has had a flat or
negative audit, so a fixed gate set selects noise. The new test (fresh gate placements each round, with parent
and child evaluated on them paired) is specified and unit-tested in its own addendum before the main arms start.

## Amendment (2026-10-30 ~09:10Z): Yangquan is not usable today; fallback for the recipe decision

Yangquan cannot read our data. Cross-region BOS reads from yq run at a few KB/s, and direct HTTP runs at
1-3 MB/s, i.e. 2-3 h per job for the checkpoint. Unblocking it needs yq-local storage or GetObject rights for
our key, which is the account owner's decision. So the 12-run sweep does not run today. Results seen before
this amendment:

* the round-1 gates of the Beijing pilot-7 pair (0.140 token, 0.180 episode);
* the round-1 pooled scores of the three cavin seed-1 replicas (-2.0, -1.0, -0.25 against their own n0);
* pilot5_curve's gates through round 3.

Fallback rule, used unless the sweep has run in full by 2026-10-31 06:00Z:

* Three recipes, each with two runs (seed 0 on Beijing, seed 1 on cavin):
  1. lr 1e-4, token loss: `bj_oft3_pilot5_curve` (legacy ratio) and `a8_oft3_pilot6_curve_matched_s1`.
  2. lr 3e-5, token loss, matched: `bj_oft3_pilot7_lr3e5` and `a8_oft3_pilot7_lr3e5_s1`.
  3. lr 3e-5, episode loss, matched: `bj_oft3_pilot7_lr3e5_ep` and `a8_oft3_pilot7_lr3e5_ep_s1`.
* For each run, D = mean over rounds 5 and 6 of (gate + audit) / 2, minus that run's own n0 (gate + audit) / 2.
  Each run is measured only against itself, so the platform offset cancels. A recipe's D is the mean of its two
  runs.
* The decision is the same as above: the highest mean D, provided it is at least +3 points, with the same
  tie-break. Otherwise no M1 main arms on LIBERO-10.
* Beijing audits do not appear in the job logs. A 1-CPU reader job prints each pilot's `accepted.jsonl` and
  `report.json` from PFS when the runs end. Those printed values are the inputs.
* If a recipe passes, the main arms run where all 15 fit soonest. That is Yangquan if it is unblocked by
  then; otherwise Beijing, as prereg v3 planned, with every arm compared only within its platform.
