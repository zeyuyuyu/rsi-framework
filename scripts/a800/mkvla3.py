"""A800: VLA study v3 (CVPR sprint) on the official OpenVLA LIBERO fine-tunes. Gate 20 + audit 20 freshly sampled
placements per task (200 + 200), paired across versions (same placements, greedy, env re-seeded per episode).
usage: mkvla3.py pilot <order>        two 2-round pilots on LIBERO-10 with tests sealed: GRPO vs success-only BC
       (pilots only choose the seed program; no test score is read)"""
import json, os, sys
H = "/data0/home/zeyuwang"
Q = f"{H}/rsi/queue"
PY = f"{H}/miniconda3/envs/vllm/bin/python"
PP = f"{H}/rsi/src2:{H}/rsi/pylib"
FIELDS = {"vla.rollout_gpus": "all", "vla.train_gpus": "first"}
CKPT = {"libero_10": f"{H}/rsi/models/openvla/openvla-7b-finetuned-libero-10",
        "libero_spatial": f"{H}/rsi/models/openvla/openvla-7b-finetuned-libero-spatial",
        "libero_object": f"{H}/rsi/models/openvla/openvla-7b-finetuned-libero-object",
        "libero_goal": "/data1/work/zeyuwang/vla_demo/ckpts/openvla-7b-finetuned-libero-goal"}
base = json.load(open(f"{H}/rsi/plans2/vla_base_goal.json"))
BC = {"curation": {"rule": "verified"}, "update": {"operator": "bc"}}


def plan(name, suite, engine, program=None, meta=None):
    p = json.loads(json.dumps(base))
    p.update(model_name=f"openvla-7b-{suite.replace('_', '-')}", suite=suite, heldout_per_task=40,
             test_inits_per_task=50, engine=engine, meta=meta or {"proposer": "fixed"})
    p["vla"].update(checkpoint=CKPT[suite], sample_procs_per_gpu=3, greedy_procs_per_gpu=4)
    if program:
        p["program"] = program
    path = f"{H}/rsi/plans2/{name}.json"
    json.dump(p, open(path, "w"), indent=2)
    return path


def job(order, name, plan_path, ngpus=2, args=()):
    j = dict(name=name, ngpus=ngpus, module="rsi.run_libero", plan=plan_path, out=f"{H}/rsi/runs2/{name}",
             gpu_fields=FIELDS, args=list(args), python=PY, pythonpath=PP, cwd=f"{H}/rsi/src2")
    json.dump(j, open(f"{Q}/pending/{order:02d}_{name}.json", "w"), indent=1)
    print("queued", name)


if sys.argv[1] == "pilot":
    order = int(sys.argv[2])
    sealed = dict(rounds=2, seed=0, seal_tests=True)
    job(order, "vla3_pilot_l10_grpo", plan("vla3_pilot_l10_grpo", "libero_10", sealed))
    job(order + 1, "vla3_pilot_l10_bc", plan("vla3_pilot_l10_bc", "libero_10", sealed, program=BC))
