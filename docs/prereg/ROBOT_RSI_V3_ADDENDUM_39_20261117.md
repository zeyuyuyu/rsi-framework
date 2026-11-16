# Addendum 39 (2026-11-17): seed 3's continuation excluded

Decision of the PI, recorded 2026-11-17 before the paper deadline. Post hoc; disclosed in the paper (Sec. 5, RL subsection) and in the supplementary material.

**What is excluded.** The continuation of seed 3 under addenda 35, 37 and 38 (`yq_oftgbx_ext_s3*`, `yq_oftgbx_mb_s3*`): its runs, evaluations and every read that includes them. Seed 3's first six rounds (`yq_oftgb_llm_harness_s3`) and every other study's seed 3 are unaffected.

**Why.** Practice success is the fraction of verified practice attempts in a round (`verified_rate` in the round records). For seed 3 it fell from 58% (round 6, the last round before the continuation) to 32% in round 7, the first round of the continuation, then to 10% in round 8 and 3% by round 15. Over the same rounds, its retained policy still scored 64.5% on validation. Seeds 1 and 2 show no such drop: seed 1 went 66%, 63%, 67% and seed 2 66–70%, 59%, 64% over rounds 6–8. Seed 3's candidates from round 8 on were trained on this collapsed data, and the gate refused all but one of them.

**What is reported.** Addenda 35, 37 and 38 are read for seeds 1 and 2 (`READ_SEEDS=1,2` in `fresh_read.py`, `goal_ext_read.py`, `addendum37_read.py`, `addendum38_read.py`). Addendum 35 at the registered stop, fresh scenes, against tuned RL with 18 blocks:

| Read | Result |
|---|---|
| One evaluation per version | +7.6 [+5.6, +9.6] |
| Three evaluations per version | +7.2 [+5.6, +8.9] |
| Official test | +4.0 [+1.4, +6.6] |
| Against RL with 36 blocks | +2.5 [+0.8, +4.3] |

The loop used 190 GPU-hours on average against RL's 230. The registered bars were set for seeds 1–3, so these numbers are reported without a pass/fail verdict against them.

**Repository.** The excluded records are removed from the current tree. Git history is unchanged. `scripts/baidu/extract_results.py` skips these run names. The launch plan `scripts/baidu/plans/yq_oftgbx_ext_s3.json` is removed, and the addendum-38 submit scripts accept seed 1 only.
