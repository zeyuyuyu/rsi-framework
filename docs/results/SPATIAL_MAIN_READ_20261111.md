# LIBERO-Spatial main study: registered one-time reads (2026-11-11 07:16Z)

Addendum 28 (official test, bars of the Goal study) and addendum 30 (sealed fresh-scene test, block `spatial_main`).
Both readers were committed before any Spatial test file existed (`scripts/report/spatial_read.py` f16c162,
`scripts/report/fresh_read.py` with the `spatial_main` block from addendum 30). Sixteen runs: fixed, nonrec,
shuffled and onebig, seeds 1-3 on the cloud pool (Y) and seed 0 on the A800 node (A). Every run has its own test
and two replicate evaluations (final = per-episode mean of three). Same episode list everywhere (digest
b476779b0bdb64b6). Seed-averaged per-episode paired bootstrap, 10,000 draws, 95% CI. Outputs:
`results/spatial_read_final_20261111.json`, `results/fresh_spatial_main_20261111.json`.

## Fresh scenes (1,000 placements, sealed, addendum 30)

Reference: initial policy, four evaluations per platform (Y 59.55%, A 59.15%).

| claim | comparison | points | 95% CI | bar | result | per seed (0, 1, 2, 3) |
|---|---|---|---|---|---|---|
| F1-spatial | fixed − initial | **+5.65** | [+4.28, +7.04] | ≥ +3 | **passes** (also over R1's +5) | +6.8, +4.8, +5.5, +5.7 |
| F2-spatial | fixed − shuffled | **+6.05** | [+4.80, +7.32] | ≥ +3 | **passes** | +9.0, +3.5, +6.8, +4.9 |
| F3-spatial | fixed − nonrec | **+4.55** | [+3.38, +5.73] | ≥ +2 | **passes** | +4.7, +6.1, +3.0, +4.4 |
| F5-spatial | fixed − onebig | +0.38 | [−0.60, +1.38] | ≥ +2 | fails (tie) | −0.7, +0.5, +1.3, +0.4 |
| noise | reference halves | −0.4 (Y), +0.4 (A) | | | | |

Finals on the fresh scenes: fixed 65.9 / 64.3 / 65.0 / 65.2, nonrec 61.2 / 58.2 / 62.0 / 60.8, onebig
66.6 / 63.8 / 63.7 / 64.8, shuffled 56.9 / 60.8 / 58.2 / 60.3 (seeds 0-3).

## Official test (500 fixed states, addendum 28)

Pooled initial reference: Y 60.23% (12 evaluations), A 58.92% (5 evaluations).

| claim | comparison | points | 95% CI | bar | result | per seed |
|---|---|---|---|---|---|---|
| R1-spatial | fixed − reference (Y, seeds 1-3) | −0.01 | [−2.15, +2.13] | ≥ +5 | fails | +0.3, +0.4, −0.8 |
| | seed 0 (A), shown | +1.95 | [−0.28, +4.08] | | | |
| R2-spatial | fixed − shuffled (seeds 0-3) | +1.67 | [+0.18, +3.13] | ≥ +3 | fails the bar, CI above 0 | +3.5, +2.0, +0.8, +0.4 |
| R3-spatial | fixed − nonrec (seeds 0-3) | **+5.73** | [+4.12, +7.38] | ≥ +2 | **passes** | +5.3, +11.9, +3.7, +2.1 |
| R5-spatial | fixed − onebig (seeds 0-3) | −0.45 | [−1.83, +0.93] | ≥ +2 | fails (tie) | +0.7, −0.7, −0.7, −1.0 |
| noise | n0 halves | −0.0 (Y), 0.0 (A) | | | | |

Every onebig candidate was accepted by its gate, so R5-ungated equals R5. Descriptive pooling with the Goal study
(not a registered claim): R2 +1.44 [+0.35, +2.55], R3 +3.73 [+2.39, +5.02], R5 −0.34 [−1.38, +0.66].

## Against the predictions written before launch

* Addendum 30: F1 "+4 to +7, passes (70%)": held. F2 "+3 to +6 (55%)": passed, slightly above the range. F3 "+1 to
  +4 at six rounds (45%)": passed, above the range. F5 "a tie": held.
* Addendum 28: R1 "+2 to +4, under +5": under the bar, and lower than predicted (zero). R2 "about even odds at +3":
  failed. R3 "positive, under +2 at six rounds": **passed** at +5.7, the first registered pass of recursion at six
  rounds. R5 "a tie": held.

## Reading

1. On scenes it never practised, gated or audited on, the self-improvement loop lifts a Spatial policy by 5.7 points,
   on every seed, and each ingredient that defines it is needed: without a real verifier it ends 6.1 points lower
   (at its start), and with practice from the frozen initial policy 4.6 points lower. Recursion passes on both
   tests already at six rounds (on Goal it needed twelve).
2. On the official 500 fixed states the same policies show no gain over the reference (−0.01). The two tests disagree
   by about 5.7 points on `fixed − initial`, while recursion and the plain-RL tie agree across them. The fresh test is
   the larger sample (1,000 vs 500 episodes) and is drawn by the same sampler the loop practises on; the official
   states are a fixed list. Both are reported, and the paper states the disagreement.
3. One round of plain RL at equal compute ties the loop on both tests (+0.38, −0.45), as on Goal at six rounds.
