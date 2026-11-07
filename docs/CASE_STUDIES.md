# Case studies: a failing algorithm, and what the RSI framework does about it

These are the runs in which the plain training procedure fails and one of the framework's three recursive
mechanisms — the gate, the data recursion, the meta level — changes the outcome. Everything below is read from
released records (`results/`), including the LLM meta level's diagnoses verbatim (`results/meta_llm/*.jsonl`).
Gate and audit numbers are shown; the official test of the self-repair arms is sealed until the registered read on
2026-11-08 and is **not** part of these case studies.

中文一句话：这里收的是"普通训练流程会失败、而框架的某一层把它救回来"的运行记录——门控防崩、数值搜索/LLM 元层修复失效配方——附 LLM 每一轮的诊断原文。正式测试 11-08 读，这里只有门控级证据。

---

## Case 1 — The gate stops a collapsing recipe (LIBERO-Goal, A800 and Yangquan)

**The failing algorithm.** Behaviour cloning (BC) on the policy's own verified successes, sampled at temperature
1.6 and fitted with a unit-temperature likelihood (`update.bc_temp = unit`). This is a plausible recipe — "clone
what worked" — and it is what a practitioner would try first.

**Without the gate** (always-accept curve `a8_oftg_curve_bc_s1`, A800, seed 1; gate / audit are two disjoint
200-episode held-out sets, never used for training):

| round | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| gate (%) | 58.5 | 58.5 | 54.5 | 57.5 | 40.0 | 14.5 | 7.0 |
| audit (%) | 58.5 | 59.0 | 61.0 | 54.5 | 49.5 | 16.0 | 4.0 |

The policy sharpens onto its own hot samples and collapses after round 3. On the Yangquan platform the same curve
fell by 6.4 points (`bj_oftg_curve_bc`, `docs/results/M1_GOAL_CURVES_20261031.md`).

**With the gate** (`fixed` arm of the self-repair study: the identical recipe, but each round's child is kept only if
it does not regress on 200 fresh paired placements):

| seed | rounds accepted / refused | retained version, gate | lowest gate of any accepted version |
|---|---|---|---|
| Y s1 | 4 / 2 | r06c0, 60.0 | 55.0 (r04c0, later replaced) |
| Y s2 | 0 / 6 | n0 (start), start kept | — |
| Y s3 | 3 / 3 | r05c0, 63.0 | 59.5 |
| A s0 | 2 / 4 | r06c0, 64.5 | 57.5 |

(Source: `results/baidu/yq_oftgb_fixed_s{1,2,3}/round-0N.json`, `results/a800/runs2/a8_oftgb_fixed_s0/`.) No gated
run ends below its start. Seed 2 is the clearest case: the gate refused all six children and the start policy was
kept — the loop could not improve, but it could not be damaged either. The gate is the recursive mechanism here: the
system's own verification result decides its next version.

**What this does not show.** The gate alone does not repair the recipe; it only refuses damage. Three of four seeds
still drift upward because, under the gate, the BC children that happen to be good are kept and the bad ones are
dropped.

---

## Case 2 — The meta level repairs the recipe (self-repair study, seeds 0-3)

Same starting recipe as Case 1. Two meta levels are allowed to edit it inside the declared harness space (operator,
temperature, learning rate, steps, batch, curation rule and band, BC likelihood temperature, allocation, ...), two
candidates per round, same compute as each other; the gate decides what is kept. **S1** (`llm_harness − fixed`) and
**S2** (`llm_harness − full`) are read on the sealed test on 2026-11-08; the records below are gate-level.

### 2a. The LLM meta level: diagnosis first, then the edit

Every round the LLM reads the round records (gate scores, acceptance, per-step sampled success, share of mixed-outcome
scenes, item counts, losses) and must write a diagnosis before proposing one edited program. Its first-round
diagnoses, verbatim (`results/meta_llm/*.meta-llm.jsonl`, field `diagnosis`):

* **Y s1, round 1:** "Only the seed exists (gate 0.61) and there are no inner-loop signals, so the limiting factor is
  uncertain. The setup looks conservative: BC on verified tries at temperature 1.6 and lr 1e-5 learns from noisy
  high-temperature samples and gives no contrast signal from failures. bc_temp 'unit' also mismatches the 1.6
  sampling temperature."
* **Y s2, round 1:** "Behaviour cloning on verified tries sampled at temperature 1.6 probably trains on noisy,
  off-distribution successes. Fitting them at unit temperature mismatches how they were sampled, and lr 1e-5 with
  100 steps is likely too weak to move the gate."
* **Y s3, round 1:** "temperature 1.6 makes tries noisy, and BC with a 'unit' temperature trains on samples drawn at
  a different temperature. lr 1e-5 over 100 steps is also small, and BC on verified tries gives no negative signal."
* **A s0, round 1:** "The baseline is BC on verified tries at temperature 1.6, which is high and likely yields noisy,
  low-quality successes. BC with lr 1e-5 and 100 steps is a small update."

All four name the actual cause (the sampling/likelihood temperature mismatch and the absence of a failure signal)
without having been told it — the diagnosis behind the hand-made fix of addendum 12 is not in the prompt. Its
first proposal on every seed was the same repair: switch the operator to GRPO on mixed-outcome scenes, lower the
sampling temperature to 1.2, raise lr to 2e-5, use `progress` allocation.

### 2b. What the gate did with the LLM's proposals

| seed | round 1 LLM proposal (vs incumbent BC) | gate verdict | what followed |
|---|---|---|---|
| Y s2 | GRPO, T 1.2, lr 2e-5, 200 steps | **kept**: 64.5 vs 61.0 | rounds 2-3 refine GRPO (lr, samples, band): kept at 64.0 and 65.5; run in progress |
| Y s1 | GRPO, T 1.2, lr 2e-5, 100 steps | kept (gate rises 57 → 59.5 → 65.5 over rounds 1-3 per the LLM's own round-3 record) | later rounds tune lr / batch / band around 61-65.5; run in progress |
| A s0 | GRPO, T 1.2, lr 2e-5, 200 steps | round-1 child not kept; the round-2 GRPO child **kept**: 65.5 vs 62.5 | run in progress (round 3) |
| Y s3 | GRPO, T 1.2, lr 2e-5, 150 steps | **refused**: 60.0 vs 60.5 | the LLM then repaired BC instead: T 1.2 (refused, 59.0), `bc_temp = rollout` + lr 3e-5 (63.5, tie, not kept), **T 1.3 + lr 2e-5 (kept, 62.5)**, GRPO again (refused, 60.0), 16 tries per scene + band (kept, 64.5). Retained: r06c1, 64.5, BC at T 1.3 |

(Sources: `results/baidu/yq_oftgb_llm_harness_s{2,3}/round-0N.json`, `retained.json`; `results/meta_llm/`.) On three
of four seeds the first repair the LLM proposed was accepted by the gate and the run then stayed on GRPO; on seed 3
the gate refused the same repair twice and the LLM found a different one inside BC. Its later diagnoses are also
worth reading: from round 3 on they say the gate is "noisy (identical re-runs differ by about 0.03-0.04)" and
"plateaued around 0.61-0.65", which is exactly the mechanism we documented for the Goal study (addendum 23).

### 2c. The numeric meta level finds repairs too

Blind mutation of the same knobs, biased toward knobs that helped the gate before (`full` arm):

| seed | retained program | gate |
|---|---|---|
| Y s1 | BC unchanged (search's edits were refused or tied) | 62.5 |
| Y s2 | **switched to GRPO** (round 1 search child kept, 60.0; later children 60.5-65.0) | 65.0 |
| Y s3 | **BC with `bc_temp = rollout`** — the one-knob fix of addendum 12 — kept from round 1 | 61.0 |
| A s0 | BC unchanged; rounds 5-6 refused | 64.0 |

So the knob space contains the repair and blind search finds it about as often as the LLM does. Whether the
diagnosing meta level ends with a *better policy* than blind search (S2) or than the gate alone (S1) is what the
sealed test decides; at the gate all three arms sit within noise of each other (60-65.5).

---

## Case 3 — Recursion rescues a stalled loop (code world models, 8 rounds)

Not a failing recipe but a stalled one: with practice generated by the frozen initial model (`nonrec`), the gate
stops accepting improvements after about four rounds (2 accepted gains in rounds 5-8 across three seeds); with
practice generated by the latest model (`fixed`) it keeps accepting (8 gains). Final CRUXEval-O difference +2.83
[+1.17, +4.50] on Qwen2.5-Coder-1.5B, replicated on 7B (+2.88 [+0.94, +4.81]; LiveCodeBench-exec +4.49). Records:
`results/baidu/bj_q15_long8*`, `bj_q7b_long8*`; `docs/prereg/ADDENDUM_3_RESULT_20261027.md`.

---

## Case 4 — What the meta level could not rescue (for honesty)

On a recipe that already works (the tuned GRPO loop of the Goal study), neither meta level beats a fixed program:
R4 arms within ±1.2 points, v2 study −0.27 / +0.30. The LLM's diagnoses there are also correct ("task 0 never solved
so GRPO has no signal", "changes within gate noise"), and its edits are the ones a practitioner would try; the loop
simply reaches the same plateau under every program in the space. `docs/results/M2_V2_20261104.md`,
`M2_CAVIN_20261106.md`, addendum 23.

---

## How to reproduce the tables

```bash
# per-round gates and acceptance of any run
python - <<'EOF'
import json, glob
for r in sorted(glob.glob('results/baidu/yq_oftgb_*/round-0*.json')):
    L = [json.loads(l) for l in open(r) if l.strip()]
    print(r, 'accepted', L[0]['accepted'], [(c['node'], c['author'], c['gate']) for c in L[1:]])
EOF
# the LLM's diagnoses and proposals
python - <<'EOF'
import json
for l in open('results/meta_llm/yq_oftgb_llm_harness_s2.meta-llm.jsonl'):
    d = json.loads(l); r = json.loads(d['reply'])
    print(r['diagnosis']); print(r['proposals'][0]['procedure']['update'])
EOF
```
