# Prereg v3, addendum 31: the framework against plain training on LIBERO-Spatial

Committed 2026-11-10 before any run named here exists. Addenda 28-30 are running; no Spatial run has finished.

## Why

The question the study has to answer in one sentence is whether training a robot policy through this framework ends
better than training it without the framework. On a recipe that already works the honest answer so far is "the
same": one-shot RL at equal compute ties the gated loop on Goal (R5 −0.58, R5-long −0.38), and the one finished
Spatial seed points the same way at the gate (0.655 against 0.665). The framework's parts are a verifier, a gate, a
recursion and a meta level; what they add over plain training shows where plain training goes wrong. The record has
one such case on Goal, measured on a single run and only at the gate: the BC recipe trained without the gate falls
from 58.5% to 5.5% in six rounds (addendum 12). The Spatial self-repair study (addendum 29) has the gate-only arm
and the meta-level arm from that recipe but no arm that simply trains. This addendum adds it, with seeds and a
test-level bar.

## Design (Yangquan, seeds 1-3, source rsi_src_v30)

`yq_oftsb_nogate_s{1,2,3}`: the `bc_start` program of addendum 29 on LIBERO-Spatial, 6 rounds × 3 inner steps, the
same practice budget per round as every other arm, **every round's child kept** (`min_gate_gain` −1.0; the fresh
gates are still scored and recorded, they decide nothing). The result of plain training is the last round's policy.
Only the initial and the final policy are tested (`test_all_accepted` false). One card each, about 14 hours.

It is compared with addendum 29's runs of the same seeds: `yq_oftsb_fixed` (the gate alone) and `yq_oftsb_meta3`
(gate and meta level v3). All three spend the same rollouts and updates per candidate; `meta3` trains two candidates
per round.

## Bars (official test; final = per-episode mean of three evaluations; the fresh-scene test of addendum 30 beside it)

* **N1: gate only − plain training ≥ +10 points, CI > 0.**
* **N2: gate + meta level − plain training ≥ +10 points, CI > 0.**
* **N3: plain training − initial reference**, reported with CI.
* Reader `scripts/report/spatial_nogate_read.py`, committed with this addendum. One read, when the three runs here
  and the six addendum-29 runs they are paired with have `report.json`, both replicates and the fresh evaluation.

## Predictions, written before launch

* Plain training collapses on at least two of three seeds: final below 30%, N3 under −25. The collapse on Goal began
  in round 4; if Spatial is slower, a seed may end only moderately below its start.
* N1 and N2 pass by a wide margin (+25 or more). N2 − N1 is FS1/S1-spatial of addendum 29 and is read there.
* If plain training does not collapse on Spatial (N3 within 5 points of the start), the BC recipe is not a failing
  recipe on this suite, N1 and N2 fail, and the Spatial self-repair study loses its premise; the paper would say so
  and keep the Goal result as the only case.

## What is not changed

No registered read, bar or run changes. The equal-compute comparison on a working recipe (R5, F5: loop against
one-shot RL) stays as registered and is reported as it comes out.

## Amendment 1 (2026-11-10 19:35Z, before any run of this addendum has started): seed 0 on the A800 node

`a8_spatrep_nogate_s0` is added on the A800 node (one card, source `src12`,
`scripts/a800/mkoft_spatial_repair.py <order> nogate`), paired with `a8_spatrep_fixed_s0` and `a8_spatrep_meta3_s0`
of addendum 29. **N1 and N2 stay registered on the Yangquan seeds 1-3**; the four-seed statistic with seed 0 is
reported alongside, each seed paired within its platform.

## Operational notes (appended 2026-11-10 19:30Z; no design change)

* Registered as 13edb67 at 19:21:56Z; amendment 1 committed as c4b9c5b at 19:26:02Z (its heading says 19:35Z; the
  commit time is the record). Both were pushed before anything below.
* A800 node, queued at 19:26Z, not yet started: `a8_spatrep_nogate_s0` (order 88, one card, `src12`). It starts when a
  card frees. The Yangquan runs `yq_oftsb_nogate_s1-3` are submitted with the other long runs once tonight's
  evaluations are in the queue.
