# Prereg v3, addendum 10 (M2): the BC pilot's first independent-audit gain, a seed replicate and a shuffled control

Committed 2026-10-30 (~08:30Z) before the runs below start. The M2 BC pilot's tests stay sealed. No v3 run has
read a test result.

## What the sealed M2 BC pilot showed (`vla3_pilot_l10_bc`, A800, seed 0, 2 rounds)

The model is OpenVLA-7B's official LIBERO-10 fine-tune. The program is the default one with the BC operator on
verified successes: 160 placements, 8 samples at T = 1.5, lr 1e-5, 200 steps.

| node | gate | audit | (gate + audit) / 2 |
|---|---|---|---|
| n0 | 0.530 | 0.560 | 0.545 |
| r01c0 (accepted) | 0.555 | 0.560 | 0.558 |
| r02c0 (accepted) | 0.595 | 0.605 | **0.600 (+5.5)** |

This is the first node in the study whose audit rose with its gate. The audit never decides anything, so its
+4.5 is not a selection effect. Over 400 episodes the pooled +5.5 is about 2.5 standard errors. It is one seed
and two rounds, and the run is a pilot, so it is not a claim.

Context: every M1 (OFT, LIBERO-10, 17% start) curve so far is flat within noise. M2 starts at 55%, where far
more sampled groups are mixed. This fits the hypothesis that self-improvement is measurable from mid-range
starting success.

## Runs (sealed, A800 / cavin, the platform M2 has used throughout)

1. `vla3_pilot_l10_bc_s1`: identical to the pilot (program, 2 rounds, 2 GPUs) except engine seed 1, so its
   training placements differ. It starts now on the two GPUs the pilot freed.
2. `vla3_pilot_l10_bc_shuf`: identical to the pilot (seed 0) with `feedback = "shuffled"`. Success labels are
   permuted among each placement's 8 attempts before curation (`shuffle_feedback`). BC then trains on the same
   number of its own episodes, from the same placements, but not on the attempts that actually succeeded. This
   separates "learning from success" from "more training on its own data". It starts when two
   more cavin GPUs are free.

## Use of the results, fixed now

* **The BC gain replicates** if `bc_s1`'s r02 pooled score is at least n0's pooled + 3 points, measured on its
  own n0.
* **The gain needs real feedback** if, in addition, `bc_shuf`'s last pooled score is below the true-feedback
  pilot's (0.600) by at least 3 points.
* If both hold, the next addendum specifies a reduced M2 study:
  * the BC operator;
  * arms fixed, shuffled and onebig, plus full if compute allows;
  * 3 seeds;
  * the fresh paired gate (addendum 9);
  * the official test read once at the end.
  If either rule fails, M2 is reported as a pilot-level observation only.
