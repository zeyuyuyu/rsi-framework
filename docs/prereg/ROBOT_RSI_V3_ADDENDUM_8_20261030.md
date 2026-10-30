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
