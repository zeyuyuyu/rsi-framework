# Addendum 3 result: recursion at 8 rounds (exploratory), 2026-10-27 00:30Z

Qwen2.5-Coder-1.5B, frozen seed program, 8 rounds, seeds 1-3, Baidu AIHC. Per-problem paired, seed-averaged
(`python -m rsi.audit.compare_arms results --study long8`). The independent re-scorer agrees with the
engine's scores on 99.6-100% of test records across all six runs.

| CRUXEval-O (points) | s1 | s2 | s3 | mean | 95% CI |
| --- | --- | --- | --- | --- | --- |
| `fixed` final - initial | +4.75 | +6.00 | +7.50 | **+6.08** | [+3.58, +8.54] |
| `nonrec` final - initial | +1.38 | +3.50 | +4.62 | +3.17 | [+0.75, +5.50] |
| `fixed` - `nonrec` (final vs final) | +4.12 | +1.88 | +2.50 | **+2.83** | [+1.17, +4.50] |

Strict gate gains of accepted nodes in rounds 5-8: `fixed` 2 / 2 / 4, total 8; `nonrec` 1 / 1 / 0, total 2.

**Reading, decided in Addendum 3 before the runs:** both conditions hold. The difference is >= +1.0 with a CI
excluding 0, and `nonrec` accepts fewer gate gains in rounds 5-8. So recursion is supported at long horizon
(exploratory). The pre-registered 4-round C3 result (-0.58, not shown) stands. Read together: within about 4
rounds the frozen initial generator's practice is as good as the improving model's. After that it is used up
(the `nonrec` gate stops moving), while the recursive arm keeps finding cases at its new frontier.

Secondary suites show no fixed-vs-nonrec difference (CRUXEval-I +0.21 [-1.46, 1.87]; LCB-exec -0.49
[-3.06, 2.09]). The extra gain is on the trained task family, with no extra forgetting. LCB-exec no longer
declines at 8 rounds for either arm (`fixed` +1.32, `nonrec` +1.74, both n.s.).

## Literature check

These sources were seen through search summaries and not yet read in full.

* **Supports.** Kim et al. 2026, *Coverage Improvement and Fast Convergence of On-policy Preference
  Learning* (arXiv 2601.08421). On-policy iterative learning converges exponentially in the number of
  iterations. A learner restricted to samples from the initial policy has a slower rate, and in their
  experiments it saturates early. That is the same shape as `nonrec` vs `fixed`.
* **Caution.** *LLM-as-a-Coach* (arXiv 2607.18110) reports forgetting (IFEval drop) when the teacher is
  updated every round. Our secondary suites show no such cost relative to `nonrec`.
