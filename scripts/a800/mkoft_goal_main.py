"""A800: addendum-14 LIBERO-Goal main arm (OFT 1-traj SFT, GRPO program of addendum 11, fresh paired gates).
arms: fixed | full (numeric meta level) | llm (LLM meta level, addendum 14) | llm_harness (addendum 16) |
llm_harness_cap (addendum 19: llm_harness capped at the seed's per-step work, src7) | onebig | nonrec | shuffled.
Runs from src5 (bc_temp + LLM meta level), admit_max_used_mib 8000. The llm arm reads the gateway key from
~/.cskey on cavin (mode 600; never in a plan or log).
usage: mkoft_goal_main.py <order> <seed> <arm> [goal|spatial]   (spatial: addendum 20, run names a8_spatmain_*)"""
import json, sys
H = "/data0/home/zeyuwang"
Q = f"{H}/rsi/queue"
order, seed, arm = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
suite = sys.argv[4] if len(sys.argv) > 4 else "goal"
assert suite in ("goal", "spatial")
ARMS = {"fixed": ({}, {"proposer": "fixed"}),
        "full": ({"candidates_per_round": 2}, {"proposer": "numeric"}),
        "llm": ({"candidates_per_round": 2}, {"proposer": "llm", "base_url": "https://api.commonstack.ai/v1",
                                               "model": "anthropic/claude-sonnet-5-5", "key_file": f"{H}/.cskey",
                                               "max_calls": 24}),
        # addendum 16: the LLM meta level may also edit harness components (loss form, ratio, advantage, data band...)
        "llm_harness": ({"candidates_per_round": 2}, {"proposer": "llm", "space": "harness",
                                                        "base_url": "https://api.commonstack.ai/v1",
                                                        "model": "anthropic/claude-sonnet-5-5",
                                                        "key_file": f"{H}/.cskey", "max_calls": 24}),
        # addendum 19: same, but no procedure may do more work per inner step than the seed (scaled down onto the cap)
        "llm_harness_cap": ({"candidates_per_round": 2}, {"proposer": "llm", "space": "harness", "budget": "seed",
                                                            "base_url": "https://api.commonstack.ai/v1",
                                                            "model": "anthropic/claude-sonnet-5-5",
                                                            "key_file": f"{H}/.cskey", "max_calls": 24}),
        "onebig": ({"rounds": 1, "inner_steps": 18}, {"proposer": "fixed"}),
        "nonrec": ({"recursive": False}, {"proposer": "fixed"}),
        "shuffled": ({"feedback": "shuffled"}, {"proposer": "fixed"})}
assert arm in ARMS
engine_extra, meta = ARMS[arm]
name = f"a8_goalmain_{arm}_s{seed}" if suite == "goal" else f"a8_spatmain_{arm}_s{seed}"
src = {"llm_harness": f"{H}/rsi/src6",          # src6 = src5 + harness components
       "llm_harness_cap": f"{H}/rsi/src7"}.get(arm, f"{H}/rsi/src5")   # src7 = src6 + budget cap (addendum 19)
vla = {"model_family": "oft", "checkpoint": f"{H}/rsi/models/oft/Openvla-oft-SFT-libero-{suite}-traj1",
       "python": f"{H}/miniconda3/envs/openvla/bin/python", "openvla_root": f"{H}/rsi/simplevla_rl",
       "rollout_gpus": [0], "train_gpus": [0], "greedy_procs_per_gpu": 4, "sample_procs_per_gpu": 3,
       "admit_max_used_mib": 8000, "ratio_mode": "matched", "loss_agg": "episode"}
program = {"curriculum": {"cases": 64}, "solver": {"temperature": 1.6},
           "update": {"steps": 100, "batch": 64, "lr": 3e-5}}
if arm.startswith("llm_harness"):     # the run's own settings, written into the program so the meta level can edit them
    program["update"].update(ratio="matched", loss_agg="episode", bc_temp="unit")
    program["curation"] = {"adv": "center"}
engine = dict({"rounds": 6, "inner_steps": 3, "gate_mode": "fresh_paired", "seed": seed}, **engine_extra)
plan = {"model_name": f"oft-sft-libero-{suite}-traj1", "vla": vla, "suite": f"libero_{suite}", "tasks": list(range(10)),
        "heldout_per_task": 40, "test_inits_per_task": 50, "engine": engine, "meta": meta, "program": program}
plan_path = f"{H}/rsi/plans2/{name}.json"
json.dump(plan, open(plan_path, "w"), indent=2)
job = dict(name=name, ngpus=1, module="rsi.run_libero", plan=plan_path, out=f"{H}/rsi/runs2/{name}",
           gpu_fields={"vla.rollout_gpus": "all", "vla.train_gpus": "first"}, args=[],
           python=f"{H}/miniconda3/envs/vllm/bin/python", pythonpath=f"{src}:{H}/rsi/pylib", cwd=src)
json.dump(job, open(f"{Q}/pending/{order:02d}_{name}.json", "w"), indent=1)
print("queued", name)
