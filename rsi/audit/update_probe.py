"""Did a trained OFT adapter move the policy, and in the direction GRPO pushes? (openvla env, one GPU)

On the sampled episodes of one rollout call (a round's training data), for every mixed case (some attempts
succeeded, some failed): the log-prob of the executed action tokens at the rollout temperature under the base
policy and under the adapter, and greedy-token agreement between the two on the same frames. GRPO should raise
the log-prob of above-average attempts (advantage > 0) and lower it for below-average ones.

Queue-runner interface (python -m rsi.audit.update_probe --plan P --out O ...); the plan supplies checkpoint,
openvla_root and the worker python is the current interpreter:
    --adapter DIR      trained adapter (ckpt-rNNcK)
    --call DIR         rollout call directory whose episodes/ were the training data
    --max-episodes N   cap (default 96), balanced over mixed cases
"""
import argparse
import collections
import json
import random
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--call", required=True)
    ap.add_argument("--max-episodes", type=int, default=96)
    ap.add_argument("--temperature", type=float, default=1.6)
    args = ap.parse_args()
    plan = json.loads(Path(args.plan).read_text())
    ckpt, root = plan["vla"]["checkpoint"], plan["vla"]["openvla_root"]
    # same interpreter state as the rollout workers (PYTHONNOUSERSITE=1): ~/.local carries an onnx that breaks
    # the openvla env's torchvision import
    import site
    user_site = site.getusersitepackages()
    sys.path[:] = [p for p in sys.path if not p.startswith(user_site)]
    here = Path(__file__).resolve().parents[1] / "backends" / "openvla_oft"
    sys.path.insert(0, str(here))
    import numpy as np
    import torch
    from rollout_worker import SPACER, load_policy
    from train_worker import FIRST_ACTION_ID, action_logits, token_mask

    by_case = collections.defaultdict(list)
    for p in sorted(Path(args.call, "episodes").glob("*.npz")):
        with np.load(p) as d:
            by_case[p.stem.rsplit("-a", 1)[0]].append((p, float(d["success"])))
    mixed = {c: v for c, v in by_case.items() if 0 < sum(s for _, s in v) < len(v)}
    rng = random.Random(0)
    picks = []
    for c in sorted(mixed):
        mean = sum(s for _, s in mixed[c]) / len(mixed[c])
        picks += [(c, p, s, s - mean) for p, s in mixed[c]]
    rng.shuffle(picks)
    picks = picks[:args.max_episodes]

    def logprobs(vla, processor, d):
        text = f"In: What action should the robot take to {str(d['task']).lower()}?\nOut:"
        ids = list(processor.tokenizer(text, add_special_tokens=True).input_ids)
        if ids[-1] != SPACER:
            ids.append(SPACER)
        n = int(len(d["executed"]))
        lps, greedy = [], []
        for a in range(0, n, 16):
            frames = list(d["frames"][a:a + 16])
            with torch.no_grad():
                logits = action_logits(vla, processor, ids, frames).float()
            tok = torch.tensor(d["tokens"][a:a + 16] - FIRST_ACTION_ID, device=logits.device)
            lp = torch.log_softmax(logits / args.temperature, -1).gather(-1, tok.unsqueeze(-1)).squeeze(-1)
            lps.append(lp.cpu().numpy())
            greedy.append(logits.argmax(-1).cpu().numpy())
        mask = token_mask(d["executed"])
        return np.concatenate(lps)[mask], np.concatenate(greedy)[mask]

    rows = {}
    for label, adapter in (("base", None), ("adapter", args.adapter)):
        vla, processor = load_policy(ckpt, adapter, root)
        for c, p, s, adv in picks:
            with np.load(p) as d:
                lp, g = logprobs(vla, processor, d)
            rows.setdefault(p.stem, dict(case=c, success=s, advantage=adv))[label] = (float(lp.mean()), g)
        del vla
        torch.cuda.empty_cache()
    out_rows = []
    for name, r in rows.items():
        (lb, gb), (la, ga) = r["base"], r["adapter"]
        out_rows.append(dict(episode=name, case=r["case"], success=r["success"], advantage=r["advantage"],
                             logprob_base=lb, logprob_adapter=la, delta=la - lb,
                             greedy_agreement=float((gb == ga).mean())))
    pos = [r["delta"] for r in out_rows if r["advantage"] > 0]
    neg = [r["delta"] for r in out_rows if r["advantage"] < 0]
    adv = np.array([r["advantage"] for r in out_rows])
    dl = np.array([r["delta"] for r in out_rows])
    summary = dict(episodes=len(out_rows), mixed_cases=len(mixed),
                   mean_delta_positive_advantage=float(np.mean(pos)) if pos else None,
                   mean_delta_negative_advantage=float(np.mean(neg)) if neg else None,
                   corr_advantage_delta=float(np.corrcoef(adv, dl)[0, 1]) if len(out_rows) > 2 else None,
                   mean_greedy_agreement=float(np.mean([r["greedy_agreement"] for r in out_rows])),
                   temperature=args.temperature, adapter=args.adapter, call=args.call)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "update_probe.json").write_text(json.dumps(dict(summary=summary, rows=out_rows), indent=2))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
