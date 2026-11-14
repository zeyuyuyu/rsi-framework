# Fig. 2 (framework diagram): what it must show after the 11-14 rewrite

The current Figma figure (`fig_framework.pdf` on Overleaf, by yli3708) was drawn for the old Section 3. Sections 3-4
now read: **Problem formulation** (task instance, policy = artifact, training program = harness, success rule) and
**Framework** with three subsections, one per decision of a round. The figure should follow that order.

## The workflow of one round (Algorithm 1, in this order)

1. **Program adaptation (meta level)**. A proposer reads the *records of completed rounds* and returns c−1 alternative programs inside 𝒫. Together with the incumbent P* they form the candidate programs P₁…P_c. Proposer options: `fixed` (off: incumbent only, c = 1), numeric search (`full`), LLM (`llm`), LLM with workspace (`llm_harness`). c = 2 when adaptation is on. *The proposer runs before the parent is evaluated, so it never sees this round's validation scores.*
2. **Draw fresh validation instances G_r** and score the parent θ* on them (g*).
3. **Learning from self-generated experience**, for each candidate program P_i, starting from θ_i ← θ*, **3 training blocks**:
   - generator θ_gen = θ_i (recursive) or θ₀ (`nonrec`)
   - sample task instances under P_i; K = 8 rollouts each at temperature T = 1.6
   - label each attempt with the success rule v (or labels permuted within each instance: `shuffled`)
   - select data (`mixed_groups` for GRPO / `verified` for BC) and update θ_i (LoRA, 100 optimiser steps; only the adapter carries over between blocks)
   - then score θ_i on G_r (greedy) → g_i
4. **Selecting policy updates (gate)**: i* = argmax g_i; if g_i* ≥ g*, retain (θ_i*, P_i*), else keep the parent (`nogate`: always accept).
5. The **retained version (θ*, P*)** starts the next round: its weights generate the next experience (data recursion) and its program trains the next candidates.
6. Outside the loop: audit (recorded, never decides) and the two **sealed tests** (official 500 episodes, fresh 1,000), read once after every run ended.

## Switches to mark (each control changes exactly one of these)

| Mark | Switch | Settings |
|---|---|---|
| ① | labels | real / shuffled within instance (`shuffled`) |
| ② | experience generator | latest candidate (recursive) / frozen θ₀ (`nonrec`) |
| ③ | selection | gate / always accept (`nogate`) |
| ④ | program adaptation | off (`fixed`) / numeric (`full`) / LLM (`llm`) / LLM + workspace (`llm_harness`) |
| (schedule) | rounds | R rounds of 3 blocks / one round of 18 or 36 blocks (`onebig`, one-shot RL) |

## Label changes in the current figure

| Current label | Replace with |
|---|---|
| Outer Loop · Recursive Self-Improvement | One round of recursive self-improvement |
| Meta · Recipe Proposal | Program adaptation (meta level) |
| Fixed / LLM / Numeric Search | off (fixed) / numeric search / LLM / LLM + workspace |
| Candidate Recipe Pᵢ | Candidate program Pᵢ |
| ④ Recipe Adaptation | ④ Program adaptation: off / numeric / LLM |
| Inner Loop / Policy Training | Learning from self-generated experience (3 training blocks per candidate) |
| Tasks: Sample fresh instances | Sample task instances c = (ℓ, x₀) |
| Verify: Oracle verification | Label: success rule v(c, τ) |
| ① Verifier: True / Shuffled | ① Labels: real / shuffled |
| Curate: Mixed / verified | Select data: mixed groups (GRPO) / successes (BC) |
| Update: GRPO / SFT / BC | Update (LoRA): GRPO / BC  (no SFT in the loop) |
| Repeat 3 training steps / round | 3 training blocks per candidate |
| Paired Evaluation: Current v.s. Candidates | Selecting policy updates: parent vs. candidates on fresh instances G_r |
| Best Candidate ≥ Current? | Best candidate ≥ parent? |
| Adopt candidate / Keep current | Retain (θᵢ*, Pᵢ*) / Keep parent |
| Round Records: Training Summary, Gate Scores / Decisions | Records of completed rounds (programs, gate scores, decisions, training statistics) → proposer |
| Retained Policy & Recipe (θ*, P*) | Retained version (θ*, P*) = policy (artifact) + training program (harness) |
| (missing) | Sealed tests (official 500, fresh 1,000), read once after all runs |

Keep: "Supported Domain: Robotic Control, LIBERO + OpenVLA-OFT", "② Generator: latest θᵢ / frozen θ₀", "③ Selection: Gated / Always Accept", "Rollout: K attempts with θ_gen".

## Parameters (seed program, frozen before the main runs)

| Parameter | Value |
|---|---|
| policy | OpenVLA-OFT 7B, action chunks of 8 (56 discrete tokens), LoRA r = 32 |
| start | supervised fine-tune on one demonstration per task (≈59% Goal, 60% Spatial) |
| update operator | GRPO, learning rate 3×10⁻⁵, matched-ratio log-probabilities, episode-balanced loss |
| per training block | 64 instances × K = 8 attempts at T = 1.6; 100 optimiser steps, batch 64 |
| round | 3 training blocks per candidate; 6 rounds (12 in the long runs) |
| candidates per round | 1 (adaptation off), 2 (numeric or LLM proposer) |
| gate | 20 instances per task = 200 episodes, greedy, new instances every round |
| audit | 200 more episodes, recorded only |
| sealed tests | official: 50 states × 10 tasks = 500 episodes; fresh: 1,000 sampled placements |
| LLM proposer | Claude Sonnet; knob space 10 hyperparameters; harness space + 9 procedure components |
| suites | LIBERO-Goal, LIBERO-Spatial (and LIBERO-10 for Fig. 5) |
