# Prereg v3, addendum 11 (M1 on LIBERO-Goal): the same model family from a mid-range start, GRPO vs BC

Committed 2026-10-30 (~10:00Z) before any LIBERO-Goal run. No v3 run has read a test result.

## Why

OFT's 1-trajectory SFT on LIBERO-10 starts at 17-19%. Every curve on it is flat within noise so far:

* pooled changes between -2.75 and +0.5 points;
* three recipes;
* two seeds per recipe, on Beijing and cavin.

At that rate most sampled groups are all-fail, so few carry a learning signal. The one positive pilot signal in
the study is M2 BC: OpenVLA-7B starting at 55%, pooled +5.5 after 2 rounds, with its audit rising. Its
paired-bootstrap CI still includes 0, and replication is under way (addendum 10).

SimpleVLA-RL reports that the 1-trajectory OFT SFT averages ~49% over the four LIBERO suites against 17.3% on
LIBERO-10 (arXiv 2509.09674). So the other three suites start at ~59% on average. LIBERO-Goal tests the same
model family, trainer and framework from a mid-range start. If it does not move either, the conclusion is about
our training budget, not the starting point.

## Pilots (sealed, Beijing, 1 GPU each, seed 0)

Checkpoint: `Haozhan72/Openvla-oft-SFT-libero-goal-traj1`, A800 weights digest 48fd2bdd…0ed5. Suite
`libero_goal`, tasks 0-9. Gate and audit are 200 + 200 sampled placements, and the official 500 stay sealed.
Each run is an always-accept curve of 6 rounds x 3 inner on-policy steps of 64 placements, 8 samples at T = 1.6,
and 100 steps of batch 64.

| run | update |
|---|---|
| `bj_oftg_curve_grpo` | GRPO lr 3e-5, matched ratio, episode-balanced loss |
| `bj_oftg_curve_bc` | BC on verified successes (lr 1e-5), the M2 operator |

GRPO uses the pilot-7 settings whose gates led so far. They were chosen before any of their audits or late
rounds were seen.

## Use of the results, fixed now

* For each run, D = mean over rounds 5 and 6 of (gate + audit) / 2, minus its n0 (gate + audit) / 2.
* If either run reaches D >= +3, the LIBERO-Goal main arms are specified next. They use that operator (the
  higher D if both qualify, BC on a tie within 1 point as the simpler update), the five prereg-v3 arms, seeds
  1-3, and the fresh paired gate (addendum 9).
* If neither reaches +3, LIBERO-Goal is reported next to LIBERO-10 as a negative result at this budget.
* The audits come from the PFS reader job, as in the addendum-8 amendment.

Amendment (2026-10-30 ~14:15Z, before any LIBERO-Goal result): the Beijing Goal pilots are waiting for CPU,
and a cavin GPU is free. So seed-1 replicas run on cavin as they become possible:
`a8_oftg_curve_bc_s1` now, and `a8_oftg_curve_grpo_s1` when a further GPU frees (`scripts/a800/mkoft_goal.py`,
src3, the same programs, `admit_max_used_mib` 8000). The rule above is applied per operator to the mean D over
the runs available by 2026-11-01 12:00Z: Beijing seed 0 and cavin seed 1, each against its own n0.

Amendment 2 (2026-10-30 ~21:05Z). This is after round 3 of `bj_oftg_curve_grpo` was seen, and before any
result from the run added here. A Beijing slot is free, and no cavin GPU is free for `a8_oftg_curve_grpo_s1`
(still queued). So `bj_oftg_curve_grpo_s2` runs on Beijing now: the same GRPO program, seed 2
(`mkplans_vla.py oftg_rep 2 grpo`). A run started now cannot reach rounds 5-6 by 2026-11-01 12:00Z, so it is
**not** part of the decision rule above, which is unchanged. It is a seed replication, read the same way (D at
rounds 5-6 against its own n0) and reported next to the rule's runs whatever it shows. The cavin seed-1
replica keeps its place in the rule if it is available by the deadline.

Amendment 3 (2026-10-31 ~02:05Z). This comes after `bj_oftg_curve_grpo` finished; its gates are seen, its
audits at rounds 5-6 are not yet read. The Beijing slot it held is free. So `bj_oftg_curve_grpo_s3` runs now:
the same GRPO program, seed 3 (`mkplans_vla.py oftg_rep 3 grpo`). Like seed 2 (amendment 2), it is outside the
decision rule, which is unchanged. It is a seed replication, read the same way and reported whatever it shows.
