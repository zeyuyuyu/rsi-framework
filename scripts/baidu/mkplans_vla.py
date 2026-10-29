"""Robotics plans for AIHC (run_vla.sh rewrites checkpoint / python / openvla_root / gpus on the node).
usage: mkplans_vla.py oft_base | oft_pilot | oft_pilot2 | oft_main <grpo|bc>   -> writes plans/<name>.json here, uploads to BOS plans/
  oft_base   M1 starting point (OFT 1-demo SFT, LIBERO-10): 500 official episodes, --baseline-only
  oft_pilot  the two sealed 2-round pilots of prereg v3 (GRPO on mixed groups vs success-only BC); tests are
             never read, gate + audit only, to choose the seed program for addendum 1
  oft_pilot2 addendum 1 extra sealed pair: GRPO at lr 5e-5 and 1e-4, otherwise the pilot program
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
elif sys.argv[1] == "oft_main" and sys.argv[2:3] in (["grpo"], ["bc"]):
    seed_program = OFT_PROGRAM if sys.argv[2] == "grpo" else merge(OFT_PROGRAM, BC)
    full_budget = {"curriculum": {"cases": 160 * 6}, "curation": {"budget": 400 * 6},
                   "update": {"steps": OFT_PROGRAM["update"]["steps"] * 6}}
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
