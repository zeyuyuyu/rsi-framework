"""Is the PPO ratio 1 before the first update? (openvla env, one GPU)

Reruns a recorded OFT GRPO train spec for a few steps under each ratio mode of the train worker and reports
the step-1 log-ratio: with no update applied yet, any deviation is numerical (bf16 forwards whose batch
neighbours differ between the old-log-prob pass and the training pass).

Queue-runner interface (python -m rsi.audit.ratio_check --plan P --out O ...):
    --spec PATH     train_spec.json of a recorded train call
    --steps N       optimizer steps per mode (default 3)
    --modes A,B     ratio modes to run (default legacy,matched)
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--steps", type=int, default=3)
    ap.add_argument("--modes", default="legacy,matched")
    args = ap.parse_args()
    plan = json.loads(Path(args.plan).read_text())
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(plan["vla"]["rollout_gpus"][0]), PYTHONNOUSERSITE="1")
    worker = Path(__file__).resolve().parents[1] / "backends" / "openvla_oft" / "train_worker.py"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for mode in args.modes.split(","):
        spec = json.loads(Path(args.spec).read_text())
        spec["update"] = dict(spec["update"], steps=args.steps, ratio=mode)
        spec["output"] = str(out / f"adapter-{mode}")
        spec_path = out / f"spec-{mode}.json"
        spec_path.write_text(json.dumps(spec, indent=1))
        log = out / f"log-{mode}.txt"
        with open(log, "w") as f:
            code = subprocess.call([sys.executable, str(worker), str(spec_path)], stdout=f, stderr=subprocess.STDOUT,
                                   env=env)
        if code != 0:
            summary[mode] = dict(code=code)
            continue
        receipt = json.loads((out / f"adapter-{mode}" / "receipt.json").read_text())
        extra = receipt["extra"]
        summary[mode] = dict(step1=extra.get("step1_logratio"), clipfrac=extra["clipfrac"], losses=extra["losses"],
                             seconds=receipt["seconds"])
    (out / "ratio_check.json").write_text(json.dumps(dict(spec=args.spec, steps=args.steps, modes=summary), indent=2))
    print(json.dumps(summary))
    if any("code" in v for v in summary.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
