# VLA addendum 1: the noise-floor bar (committed before any VLA RSI test score is read)

Written 2026-10-26 08:20Z. The two replicates of the initial OpenVLA-7B (libero-goal) on the 500 official
episodes are in; no RSI-trained VLA version has been evaluated on the test set (the 1-round pilot runs with
tests sealed, and the 8 arms are still on hold).

## What the replicates show

| | success |
| --- | --- |
| replicate 0 | 74.8% |
| replicate 1 | 76.4% |
| episodes whose outcome differs | 62 / 500 = 12.4% (35 fail->success, 27 success->fail) |
| net difference | +1.6 points, exact McNemar p = 0.37 |

Flips concentrate in tasks 3, 0 and 5 (17, 12, 11 of 50 episodes each). Greedy decoding is unbatched and
the simulator is re-seeded per episode, so the remaining run-to-run variation comes from GPU numerics over
300-step closed-loop rollouts. This is far more than the 1/32 seen in the earlier reproducibility check.

## The bar as written cannot be met, and what is reported instead

V1 in VLA_PREREG_20261026.md requires "the gain exceeds 2x the measured run-to-run flip rate". Read
literally, a 12.4% flip rate gives a 24.8-point bar, which is above any plausible effect and was not the
intent. The flip rate counts changes in both directions, while a gain is a net difference. The intended
reading, used from now on, is:

* The gain must exceed 2x the net replicate difference: 2 x 1.6 = 3.2 points. This sits next to the
  already-required +3.0 points and paired McNemar p < 0.05 in both seeds.

The literal reading is also reported, and will fail.

Two further rules:

* Every RSI comparison stays paired per episode (McNemar), so flips in both directions count as noise.
* Any change smaller than the replicate band of +/-1.6 points is reported as noise.
