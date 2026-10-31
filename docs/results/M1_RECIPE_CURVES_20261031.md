# M1 (OFT 1-traj SFT, LIBERO-10): recipe curves under the addendum-8 fallback rule (2026-10-31)

Pilots are sealed, so no test was read. Pooled score S = (gate + audit) / 2, 400 episodes.
D = mean S over rounds 5-6 minus the run's own n0 S. The rule asks for a recipe mean D of at least +3.

## Beijing, seed 0 (final)

n0 for all three: gate 0.165, audit 0.215, S 0.190 (Beijing evaluation is deterministic).

| recipe | run | S by round 1 → 6 | D |
|---|---|---|---|
| lr 1e-4, token, legacy ratio | `bj_oft3_pilot5_curve` | 0.170, 0.180, 0.1875, 0.2175, 0.2075, 0.1975 | **+1.25** |
| lr 3e-5, token, matched | `bj_oft3_pilot7_lr3e5` | 0.1625, 0.180, 0.1875, 0.1775, 0.175, 0.1825 | **-1.1** |
| lr 3e-5, episode, matched | `bj_oft3_pilot7_lr3e5_ep` | 0.195, 0.205, 0.1825, 0.1975, 0.180, 0.215 | **+0.75** |

Settings were confirmed from the runs' receipts: `loss_agg` episode and `ratio_mode` matched where declared.

## cavin, seed 1 (in progress at the time of writing)

| recipe | run | n0 S | S by round so far |
|---|---|---|---|
| lr 1e-4, token, matched | `a8_oft3_pilot6_curve_matched_s1` | 0.2025 | 0.200, 0.190, 0.190, 0.1875, 0.200, 0.185 (final; **D -1.00**) |
| lr 3e-5, token, matched | `a8_oft3_pilot7_lr3e5_s1` | 0.2025 | 0.1825, 0.150, 0.185, 0.1975, 0.1925 |
| lr 3e-5, episode, matched | `a8_oft3_pilot7_lr3e5_ep_s1` | 0.200 | 0.190, 0.175, 0.215, 0.1725, 0.185 |

## Reading so far

* Every curve stays within about ±3 points of its start for 18 on-policy steps (9k sampled episodes). No recipe
  approaches the +3 bar on Beijing.
* Round-to-round changes of 2-4 points are noise. A 400-episode paired comparison has an SE of about 3 points,
  because ~40% of episodes flip between nearby policies, and even identical weights flip 13.6% on the A800.
* Arithmetic check (2026-10-30 22:20Z): for the lr-1e-4 recipe to average +3 with Beijing's +1.25, the cavin
  seed-1 run needs D >= +4.75, i.e. a round-6 S of about 0.30 after r05 0.200. The other two recipes start from
  Beijing D of -1.1 and +0.75 and are at or below their n0 on cavin. The rule is still applied formally at round 6.
* lr-1e-4 recipe, final: Beijing D +1.25 and cavin D -1.00, mean **+0.13**, below the +3 bar.
* The addendum-8 decision is taken when the cavin seed-1 runs finish rounds 5-6. Unless they reach about +5,
  no recipe can average +3. In that case the rule says: no M1 main arms on LIBERO-10, and the result is reported
  as a negative finding at this budget (18 steps × 512 episodes, LoRA r32, 1 GPU per run).
