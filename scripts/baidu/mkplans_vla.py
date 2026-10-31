"""Robotics plans for AIHC (run_vla.sh rewrites checkpoint / python / openvla_root / gpus on the node).
usage: mkplans_vla.py oft_base | oft_pilot | oft_pilot2 | oft_pilot3 | oft_pilot4 | infl | oft_main <grpo|bc> [lr]   -> writes plans/<name>.json here, uploads to BOS plans/
  oft_base   M1 starting point (OFT 1-demo SFT, LIBERO-10): 500 official episodes, --baseline-only
  oft_pilot  the two sealed 2-round pilots of prereg v3 (GRPO on mixed groups vs success-only BC); tests are
             never read, gate + audit only, to choose the seed program for addendum 1
  oft_pilot2 addendum 1 extra sealed pair: GRPO at lr 5e-5 and 1e-4, otherwise the pilot program
  oft_pilot3 addendum 3 sealed pair, 1 round: GRPO lr 1e-4 with 400 and 1000 update steps
  oft_pilot5 addendum 5 sealed pair: 6 rounds x 3 inner on-policy steps of 64 placements, gated vs always-accept
  oft_pilot6 addendum 6: pilot5_curve with vla.ratio_mode "matched" (old log-probs from the training micro-batches)
  oft_pilot7 addendum 7: pilot5_curve at lr 3e-5 with the matched ratio, token vs episode-balanced loss
  yq_sweep   addendum 8: lr {1e-5,3e-5,1e-4} x loss {token,episode} x seeds {1,2} always-accept curves (Yangquan)
  yq_main    addendum 9: 5 arms x seeds 1-3 on Yangquan, fresh paired gates, recipe from the addendum-8 rule
  oftg_pilot addendum 11: OFT on LIBERO-Goal, GRPO (lr 3e-5, matched, episode loss) vs BC curves, seed 0
  oftg_rep   addendum 11 amendment 2: a further seed replica of one oftg_pilot curve (oftg_rep <seed> <grpo|bc>)
  goal_main  LIBERO-Goal main arms (5 arms x seeds 1-3, fresh paired gates) with the operator addendum 11 picks
  infl       train-on-test inflation replication on Baidu: SFT start and SimpleVLA-RL RL checkpoint, plans with
             500 fresh placements (heldout_per_task 50) and base-version receipts for --heldout-eval
  oft_main   prereg v3 main arms on LIBERO-10, seeds 1-3, 6 rounds, seed program frozen by addendum 1:
             fixed | full (numeric proposer, 2 candidates/round) | nonrec | shuffled | onebig (one round with
             the summed 6-round budget: cases, curation budget and update steps x6, budget_scale 6)"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "plans")
os.makedirs(OUT, exist_ok=True)
VLA = {"model_family": "oft", "checkpoint": "@node", "python": "@node", "openvla_root": "@node",
       "rollout_gpus": [0], "train_gpus": [0], "greedy_procs_per_gpu": 5, "sample_procs_per_gpu": 3}
# SimpleVLA-RL samples at T=1.6; an OFT training item is one 8-step chunk (56 tokens), ~40 per episode
OFT_PROGRAM = {"solver": {"temperature": 1.6}, "update": {"steps": 100, "batch": 64, "lr": 1e-5}}
BC = {"curation": {"rule": "verified"}, "update": {"operator": "bc"}}


def write(name, **kw):
    p = dict(model_name="oft-sft-libero10-traj1", vla=dict(VLA), suite="libero_10", tasks=list(range(10)),
             heldout_per_task=40, test_inits_per_task=50)
    p.update(kw)
    path = os.path.join(OUT, f"{name}.json")
    json.dump(p, open(path, "w"), indent=2)
    st = subprocess.run([sys.executable, os.path.join(HERE, "bos_rw.py"), "put", "bos-research-team",
                         f"shitianyu-rsi/plans/{name}.json", path, "application/json"], capture_output=True, text=True)
    print(name, st.stdout.strip()[:80])


def merge(a, b):
    out = json.loads(json.dumps(a))
    for k, v in b.items():
        out.setdefault(k, {}).update(v)
    return out


if sys.argv[1] == "oft_base":
    write("bj_oft_base_l10", heldout_per_task=2)
elif sys.argv[1] == "oft_pilot":
    sealed = dict(rounds=2, seed=0, seal_tests=True)
    write("bj_oft3_pilot_l10_grpo", engine=sealed, meta={"proposer": "fixed"}, program=OFT_PROGRAM)
    write("bj_oft3_pilot_l10_bc", engine=sealed, meta={"proposer": "fixed"}, program=merge(OFT_PROGRAM, BC))
elif sys.argv[1] == "oft_pilot2":
    sealed = dict(rounds=2, seed=0, seal_tests=True)
    for tag, lr in (("lr5e5", 5e-5), ("lr1e4", 1e-4)):
        write(f"bj_oft3_pilot2_l10_{tag}", engine=sealed, meta={"proposer": "fixed"},
              program=merge(OFT_PROGRAM, {"update": {"lr": lr}}))
elif sys.argv[1] == "oft_pilot3":
    sealed = dict(rounds=1, seed=0, seal_tests=True)
    for steps in (400, 1000):
        write(f"bj_oft3_pilot3_l10_s{steps}", engine=sealed, meta={"proposer": "fixed"},
              program=merge(OFT_PROGRAM, {"update": {"lr": 1e-4, "steps": steps}}))
elif sys.argv[1] == "oft_pilot4":           # addendum 4: 12 short on-policy rounds of 64 placements
    write("bj_oft3_pilot4_short", engine=dict(rounds=12, seed=0, seal_tests=True), meta={"proposer": "fixed"},
          program=merge(OFT_PROGRAM, {"curriculum": {"cases": 64}, "update": {"lr": 1e-4}}))
elif sys.argv[1] == "oft_pilot5":
    short = merge(OFT_PROGRAM, {"curriculum": {"cases": 64}, "update": {"lr": 1e-4}})
    for tag, extra in (("gated", {}), ("curve", {"min_gate_gain": -1.0})):
        write(f"bj_oft3_pilot5_{tag}", engine=dict(rounds=6, inner_steps=3, seed=0, seal_tests=True, **extra),
              meta={"proposer": "fixed"}, program=short)
elif sys.argv[1] == "oft_pilot6":
    short = merge(OFT_PROGRAM, {"curriculum": {"cases": 64}, "update": {"lr": 1e-4}})
    write("bj_oft3_pilot6_curve_matched", vla=dict(VLA, ratio_mode="matched"),
          engine=dict(rounds=6, inner_steps=3, seed=0, seal_tests=True, min_gate_gain=-1.0),
          meta={"proposer": "fixed"}, program=short)
elif sys.argv[1] == "oft_pilot7":
    short = merge(OFT_PROGRAM, {"curriculum": {"cases": 64}, "update": {"lr": 3e-5}})
    for tag, extra in (("lr3e5", {}), ("lr3e5_ep", {"loss_agg": "episode"})):
        write(f"bj_oft3_pilot7_{tag}", vla=dict(VLA, ratio_mode="matched", **extra),
              engine=dict(rounds=6, inner_steps=3, seed=0, seal_tests=True, min_gate_gain=-1.0),
              meta={"proposer": "fixed"}, program=short)
elif sys.argv[1] == "yq_sweep":
    # addendum 8: update-recipe sweep on the Yangquan A800 pool, seeds 1-2, every curve with the matched ratio
    for lr_tag, lr in (("1e5", 1e-5), ("3e5", 3e-5), ("1e4", 1e-4)):
        for agg_tag, agg in (("tok", "token"), ("ep", "episode")):
            for seed in (1, 2):
                prog = merge(OFT_PROGRAM, {"curriculum": {"cases": 64}, "update": {"lr": lr}})
                write(f"yq_oft3_curve_lr{lr_tag}_{agg_tag}_s{seed}",
                      vla=dict(VLA, ratio_mode="matched", loss_agg=agg),
                      engine=dict(rounds=6, inner_steps=3, seed=seed, seal_tests=True, min_gate_gain=-1.0),
                      meta={"proposer": "fixed"}, program=prog)
elif sys.argv[1] == "yq_main":
    # addendum 9: the 15 M1 main arms on Yangquan with the recipe the addendum-8 rule picks
    # usage: mkplans_vla.py yq_main <lr> <token|episode>
    lr, agg = float(sys.argv[2]), sys.argv[3]
    assert agg in ("token", "episode")
    prog = merge(OFT_PROGRAM, {"curriculum": {"cases": 64}, "update": {"lr": lr}})
    vla = dict(VLA, ratio_mode="matched", loss_agg=agg)
    gated = {"rounds": 6, "inner_steps": 3, "gate_mode": "fresh_paired"}
    arms = {"fixed": ({}, "fixed"), "full": ({"candidates_per_round": 2}, "numeric"),
            "nonrec": ({"recursive": False}, "fixed"), "shuffled": ({"feedback": "shuffled"}, "fixed"),
            "onebig": ({"rounds": 1, "inner_steps": 18}, "fixed")}      # same sampling, no intermediate gate
    for seed in (1, 2, 3):
        for arm, (engine, proposer) in arms.items():
            write(f"yq_oft3_{arm}_s{seed}", vla=vla, engine=dict(gated, seed=seed, **engine),
                  meta={"proposer": proposer}, program=prog)
elif sys.argv[1] == "oftg_pilot":
    # addendum 11: OFT 1-traj SFT on LIBERO-Goal (mid-range start), GRPO vs BC always-accept curves, seed 0
    curve = dict(rounds=6, inner_steps=3, seed=0, seal_tests=True, min_gate_gain=-1.0)
    grpo = merge(OFT_PROGRAM, {"curriculum": {"cases": 64}, "update": {"lr": 3e-5}})
    bc = merge(merge(OFT_PROGRAM, BC), {"curriculum": {"cases": 64}})
    for tag, prog, extra in (("grpo", grpo, {"ratio_mode": "matched", "loss_agg": "episode"}), ("bc", bc, {})):
        write(f"bj_oftg_curve_{tag}", model_name="oft-sft-libero-goal-traj1", suite="libero_goal",
              vla=dict(VLA, **extra), engine=curve, meta={"proposer": "fixed"}, program=prog)
elif sys.argv[1] == "oftg_rep":
    # addendum 11, amendment 2: a further seed replica of one oftg_pilot curve. usage: mkplans_vla.py oftg_rep <seed> <grpo|bc>
    seed, tag = int(sys.argv[2]), sys.argv[3]
    assert tag in ("grpo", "bc") and seed > 0
    curve = dict(rounds=6, inner_steps=3, seed=seed, seal_tests=True, min_gate_gain=-1.0)
    if tag == "grpo":
        prog, extra = merge(OFT_PROGRAM, {"curriculum": {"cases": 64}, "update": {"lr": 3e-5}}), {"ratio_mode": "matched", "loss_agg": "episode"}
    else:
        prog, extra = merge(merge(OFT_PROGRAM, BC), {"curriculum": {"cases": 64}}), {}
    write(f"bj_oftg_curve_{tag}_s{seed}", model_name="oft-sft-libero-goal-traj1", suite="libero_goal",
          vla=dict(VLA, **extra), engine=curve, meta={"proposer": "fixed"}, program=prog)
elif sys.argv[1] == "yq_smoke":
    # Yangquan end-to-end check before the main arms (addendum 15): 1 round x 1 inner step of 40 placements, 20 + 20
    # gate/audit placements, tests sealed; the main-arm GRPO settings. Not a result.
    prog = merge(OFT_PROGRAM, {"curriculum": {"cases": 40}, "update": {"lr": 3e-5, "steps": 50}})
    write("yq_smoke_goal", model_name="oft-sft-libero-goal-traj1", suite="libero_goal", heldout_per_task=2,
          vla=dict(VLA, ratio_mode="matched", loss_agg="episode"),
          engine=dict(rounds=1, inner_steps=1, seed=0, seal_tests=True, min_gate_gain=-1.0),
          meta={"proposer": "fixed"}, program=prog)
elif sys.argv[1] == "goal_main":
    # the LIBERO-Goal main arms once addendum 11's rule picks an operator (specified in its own addendum before launch)
    # usage: mkplans_vla.py goal_main <grpo|bc> <prefix: bj|yq>
    op, prefix = sys.argv[2], sys.argv[3]
    assert op in ("grpo", "bc") and prefix in ("bj", "yq")
    if op == "grpo":
        prog = merge(OFT_PROGRAM, {"curriculum": {"cases": 64}, "update": {"lr": 3e-5}})
        vla = dict(VLA, ratio_mode="matched", loss_agg="episode")
    else:
        prog = merge(merge(OFT_PROGRAM, BC), {"curriculum": {"cases": 64}})
        vla = dict(VLA)
    gated = {"rounds": 6, "inner_steps": 3, "gate_mode": "fresh_paired"}
    arms = {"fixed": ({}, "fixed"), "full": ({"candidates_per_round": 2}, "numeric"),
            "nonrec": ({"recursive": False}, "fixed"), "shuffled": ({"feedback": "shuffled"}, "fixed"),
            "onebig": ({"rounds": 1, "inner_steps": 18}, "fixed")}
    for seed in (1, 2, 3):
        for arm, (engine, proposer) in arms.items():
            write(f"{prefix}_oftg_{arm}_s{seed}", model_name="oft-sft-libero-goal-traj1", suite="libero_goal",
                  vla=vla, engine=dict(gated, seed=seed, **engine), meta={"proposer": proposer}, program=prog)
elif sys.argv[1] == "yq_rsi":
    # addendum 17: Yangquan arms beyond addendum 15 -- Goal llm_harness x3 (LLM relayed through BOS, key stays on cavin)
    # and LIBERO-10 fixed vs llm_harness x2 (does a harness-editing meta level make a recipe work where fixed fails?)
    prog = merge(OFT_PROGRAM, {"curriculum": {"cases": 64}, "update": {"lr": 3e-5}})
    vla = dict(VLA, ratio_mode="matched", loss_agg="episode")
    gated = {"rounds": 6, "inner_steps": 3, "gate_mode": "fresh_paired"}
    llm_h = {"proposer": "llm", "space": "harness", "relay": True, "model": "anthropic/claude-sonnet-5-5", "max_calls": 24}
    hprog = merge(prog, {"update": {"ratio": "matched", "loss_agg": "episode", "bc_temp": "unit"},
                         "curation": {"adv": "center"}})
    for seed in (1, 2, 3):
        write(f"yq_oftg_llm_harness_s{seed}", model_name="oft-sft-libero-goal-traj1", suite="libero_goal", vla=vla,
              engine=dict(gated, seed=seed, candidates_per_round=2), meta=llm_h, program=hprog)
    for seed in (1, 2):
        write(f"yq_oftl_fixed_s{seed}", vla=vla, engine=dict(gated, seed=seed), meta={"proposer": "fixed"}, program=prog)
        write(f"yq_oftl_llm_harness_s{seed}", vla=vla, engine=dict(gated, seed=seed, candidates_per_round=2),
              meta=llm_h, program=hprog)
elif sys.argv[1] == "bj_l10_pair":
    # addendum 17 amendment: an extra LIBERO-10 pair on Beijing (deterministic evaluation), seed 3, exploratory
    prog = merge(OFT_PROGRAM, {"curriculum": {"cases": 64}, "update": {"lr": 3e-5}})
    vla = dict(VLA, ratio_mode="matched", loss_agg="episode")
    gated = {"rounds": 6, "inner_steps": 3, "gate_mode": "fresh_paired", "seed": 3}
    hprog = merge(prog, {"update": {"ratio": "matched", "loss_agg": "episode", "bc_temp": "unit"}, "curation": {"adv": "center"}})
    write("bj_oftl_fixed_s3", vla=vla, engine=dict(gated), meta={"proposer": "fixed"}, program=prog)
    write("bj_oftl_llm_harness_s3", vla=vla, engine=dict(gated, candidates_per_round=2), program=hprog,
          meta={"proposer": "llm", "space": "harness", "relay": True, "model": "anthropic/claude-sonnet-5-5", "max_calls": 24})
elif sys.argv[1] == "bj_cap":
    # addendum 19 amendment: one more compute-capped harness run on Beijing (deterministic evaluation), Goal seed 4.
    # It only adds proposal-vs-incumbent head-to-heads to H-cap; it has no fixed partner here.
    prog = merge(OFT_PROGRAM, {"curriculum": {"cases": 64}, "update": {"lr": 3e-5}})
    vla = dict(VLA, ratio_mode="matched", loss_agg="episode")
    hprog = merge(prog, {"update": {"ratio": "matched", "loss_agg": "episode", "bc_temp": "unit"}, "curation": {"adv": "center"}})
    write("bj_oftg_llm_harness_cap_s4", model_name="oft-sft-libero-goal-traj1", suite="libero_goal", vla=vla,
          engine={"rounds": 6, "inner_steps": 3, "gate_mode": "fresh_paired", "seed": 4, "candidates_per_round": 2},
          program=hprog, meta={"proposer": "llm", "space": "harness", "budget": "seed", "relay": True,
                               "model": "anthropic/claude-sonnet-5-5", "max_calls": 24})
elif sys.argv[1] == "bj_t12":
    # addendum 19 amendment 2: fixed control that applies bj cap s4's round-1 LLM edit from round 0 and never changes it
    prog = merge(OFT_PROGRAM, {"curriculum": {"cases": 64, "allocation": "progress", "floor": 0.1},
                               "solver": {"temperature": 1.2},
                               "curation": {"rule": "mixed_groups", "budget": 400, "per_case": 2, "adv": "center"},
                               "update": {"lr": 3e-5, "ratio": "matched", "loss_agg": "episode", "bc_temp": "unit"}})
    vla = dict(VLA, ratio_mode="matched", loss_agg="episode")
    write("bj_oftg_fixed_t12_s4", model_name="oft-sft-libero-goal-traj1", suite="libero_goal", vla=vla,
          engine={"rounds": 6, "inner_steps": 3, "gate_mode": "fresh_paired", "seed": 4},
          program=prog, meta={"proposer": "fixed"})
elif sys.argv[1] == "infl":
    for which, repo in (("sft", "Openvla-oft-SFT-libero10-traj1"), ("rl", "openvla-oft-libero10-traj1-rl")):
        write(f"bj_infl_{which}", model_name=f"oft-{which}-libero10-traj1", heldout_per_task=50)
        receipt = os.path.join(OUT, f"bj_infl_{which}_receipt.json")
        json.dump({"version": {"id": f"base:oft-{which}-libero10-traj1", "parent_id": None,
                               "location": f"/mnt/pfs/shitianyu-rsi/models/{repo}"}}, open(receipt, "w"))
        st = subprocess.run([sys.executable, os.path.join(HERE, "bos_rw.py"), "put", "bos-research-team",
                             f"shitianyu-rsi/plans/bj_infl_{which}_receipt.json", receipt, "application/json"],
                            capture_output=True, text=True)
        print(f"bj_infl_{which}_receipt", st.stdout.strip()[:60])
elif sys.argv[1] == "oft_main" and sys.argv[2:3] in (["grpo"], ["bc"]):
    seed_program = OFT_PROGRAM if sys.argv[2] == "grpo" else merge(OFT_PROGRAM, BC)
    if len(sys.argv) > 3:                       # lr frozen by addendum 2 (1e-4)
        seed_program = merge(seed_program, {"update": {"lr": float(sys.argv[3])}})
    if len(sys.argv) > 4:                       # update steps frozen by addendum 4
        seed_program = merge(seed_program, {"update": {"steps": int(sys.argv[4])}})
    full_budget = {"curriculum": {"cases": 160 * 6}, "curation": {"budget": 400 * 6},
                   "update": {"steps": seed_program["update"]["steps"] * 6}}
    arms = {"fixed": ({}, "fixed", seed_program, 1), "full": ({"candidates_per_round": 2}, "numeric", seed_program, 1),
            "nonrec": ({"recursive": False}, "fixed", seed_program, 1),
            "shuffled": ({"feedback": "shuffled"}, "fixed", seed_program, 1),
            "onebig": ({"rounds": 1}, "fixed", merge(seed_program, full_budget), 6)}
    for seed in (1, 2, 3):
        for arm, (engine, proposer, program, scale) in arms.items():
            write(f"bj_oft3_{arm}_s{seed}", engine=dict({"rounds": 6, "seed": seed}, **engine),
                  meta={"proposer": proposer}, program=program, budget_scale=scale)
else:
    raise SystemExit(__doc__)
