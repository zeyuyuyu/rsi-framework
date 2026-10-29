"""Robotics plans for AIHC (run_vla.sh rewrites checkpoint / python / openvla_root / gpus on the node).
usage: mkplans_vla.py oft_base | oft_pilot | oft_pilot2 | oft_pilot3 | oft_pilot4 | infl | oft_main <grpo|bc> [lr]   -> writes plans/<name>.json here, uploads to BOS plans/
  oft_base   M1 starting point (OFT 1-demo SFT, LIBERO-10): 500 official episodes, --baseline-only
  oft_pilot  the two sealed 2-round pilots of prereg v3 (GRPO on mixed groups vs success-only BC); tests are
             never read, gate + audit only, to choose the seed program for addendum 1
  oft_pilot2 addendum 1 extra sealed pair: GRPO at lr 5e-5 and 1e-4, otherwise the pilot program
  oft_pilot3 addendum 3 sealed pair, 1 round: GRPO lr 1e-4 with 400 and 1000 update steps
  oft_pilot5 addendum 5 sealed pair: 6 rounds x 3 inner on-policy steps of 64 placements, gated vs always-accept
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
