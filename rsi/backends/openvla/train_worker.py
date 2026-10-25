"""OpenVLA LoRA worker. Operators: ``bc`` and ``grpo`` over the policy's own episodes.

bc   - items {episode}; cross-entropy on the 7 action tokens (+ stop token) the
       policy itself emitted, on the exact frames it saw.
grpo - items {experience: {episode, temperature}, advantage}; the episode-level
       advantage applies to every action token of the episode; token-level
       PPO-clip against the parent policy (old log-probs computed here before
       the first update), logits scaled by the rollout temperature so the ratio
       is taken against the behaviour policy; no KL.
Prompt, spacer token, logits/labels alignment and LoRA recipe follow the
earlier validated trainer (experiments/correction/finetune/ft_train.py).
"""

import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

IGNORE = -100
SPACER = 29871


def digest(model):
    h = hashlib.sha256()
    for name, p in model.named_parameters():
        if p.requires_grad:
            h.update(name.encode())
            h.update(p.detach().float().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def main(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    sys.path.append(spec["openvla_root"])
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import torch
    import torch.nn.functional as F
    from PIL import Image
    from peft import LoraConfig, PeftModel, get_peft_model
    from rollout_worker import load_policy

    update = spec["update"]
    operator = update["operator"]
    torch.manual_seed(spec["seed"])
    rng = random.Random(spec["seed"])
    output = Path(spec["output"])
    output.mkdir(parents=True, exist_ok=False)
    vla, processor = load_policy(spec["checkpoint"], None)
    tok = processor.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else 0
    num_patches = vla.vision_backbone.featurizer.patch_embed.num_patches

    episodes = []
    for item in spec["items"]:
        exp = item if operator == "bc" else item["experience"]
        adv = 1.0 if operator == "bc" else float(item["advantage"])
        if operator == "grpo" and adv == 0.0:
            continue
        data = np.load(exp["episode"])
        if len(data["tokens"]) == 0:
            continue
        prompt = f"In: What action should the robot take to {str(data['task']).lower()}?\nOut:"
        ids = list(tok(prompt, add_special_tokens=True).input_ids)
        if ids[-1] != SPACER:
            ids.append(SPACER)
        episodes.append(dict(frames=data["frames"], tokens=data["tokens"], prompt=ids, adv=adv,
                             temperature=float(exp.get("temperature") or 1.0) or 1.0))
    index = [(e, t) for e in range(len(episodes)) for t in range(len(episodes[e]["tokens"]))]
    if not index:
        raise SystemExit("no_training_frames")

    def batch_inputs(picks):
        seqs, pixels, starts = [], [], []
        for e, t in picks:
            ep = episodes[e]
            seq = ep["prompt"] + [int(x) for x in ep["tokens"][t]] + [int(tok.eos_token_id)]
            seqs.append(seq)
            starts.append(len(ep["prompt"]))
            pixels.append(processor.image_processor.apply_transform(
                Image.fromarray(ep["frames"][t]).convert("RGB")))
        width = max(len(s) for s in seqs)
        ids = torch.full((len(seqs), width), pad, dtype=torch.long)
        att = torch.zeros((len(seqs), width), dtype=torch.bool)
        for i, s in enumerate(seqs):
            ids[i, :len(s)] = torch.tensor(s)
            att[i, :len(s)] = True
        return ids.to("cuda:0"), att.to("cuda:0"), torch.stack(pixels).to("cuda:0", torch.bfloat16), starts

    def action_logprobs(model, picks, with_eos=False):
        ids, att, pv, starts = batch_inputs(picks)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            out = model(input_ids=ids, attention_mask=att, pixel_values=pv)
        # logits at text position p (offset by the image patches) predict token p+1
        logits = out.logits[:, num_patches:-1].float()
        rows = []
        for i, ((e, t), s) in enumerate(zip(picks, starts)):
            n = 8 if with_eos else 7
            temp = episodes[e]["temperature"] if operator == "grpo" else 1.0
            lg = logits[i, s - 1:s - 1 + n] / temp
            target = ids[i, s:s + n]
            rows.append(torch.log_softmax(lg, -1).gather(-1, target.unsqueeze(-1)).squeeze(-1))
        return torch.stack(rows)

    parent = spec["parent"]
    if parent["parent_id"] is None:
        vla = get_peft_model(vla, LoraConfig(r=spec["lora_rank"], lora_alpha=spec["lora_alpha"],
                                             lora_dropout=0.0, target_modules=spec["target_modules"],
                                             init_lora_weights="gaussian"))
    else:
        vla = PeftModel.from_pretrained(vla, parent["location"], is_trainable=True)
    mb = spec["micro_batch"]
    old = None
    if operator == "grpo":
        vla.eval()
        old = {}
        with torch.no_grad():
            for b in range(0, len(index), mb):
                picks = index[b:b + mb]
                lp = action_logprobs(vla, picks)
                for k, key in enumerate(picks):
                    old[key] = lp[k].detach()
    vla.train()
    params = [p for p in vla.parameters() if p.requires_grad]
    before = digest(vla)
    opt = torch.optim.AdamW(params, lr=float(update["lr"]), weight_decay=0.0)
    steps, batch = int(update["steps"]), int(update["batch"])
    clip_lo, clip_hi = float(update.get("clip_low", 0.2)), float(update.get("clip_high", 0.28))
    order, cursor, losses, clipfrac = [], 0, [], []
    started = time.time()
    for step in range(steps):
        picks = []
        while len(picks) < batch:
            if cursor >= len(order):
                order, cursor = list(range(len(index))), 0
                rng.shuffle(order)
            picks.append(index[order[cursor]])
            cursor += 1
        opt.zero_grad(set_to_none=True)
        step_loss, clipped = 0.0, 0
        for b in range(0, batch, mb):
            chunk = picks[b:b + mb]
            if operator == "bc":
                lp = action_logprobs(vla, chunk, with_eos=True)
                loss = -lp.mean() * len(chunk) / batch
            else:
                lp = action_logprobs(vla, chunk)
                ratio = torch.exp(lp - torch.stack([old[k] for k in chunk]))
                adv = torch.tensor([episodes[e]["adv"] for e, _ in chunk], device=lp.device)[:, None]
                obj = torch.min(ratio * adv, torch.clamp(ratio, 1 - clip_lo, 1 + clip_hi) * adv)
                loss = -obj.mean() * len(chunk) / batch
                clipped += int(((ratio < 1 - clip_lo) | (ratio > 1 + clip_hi)).sum())
            if not torch.isfinite(loss):
                raise SystemExit("nonfinite_loss")
            loss.backward()
            step_loss += float(loss)
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        losses.append(step_loss)
        clipfrac.append(clipped / (7 * batch) if operator == "grpo" else 0.0)
        if (step + 1) % 10 == 0:
            print(json.dumps(dict(step=step + 1, loss=step_loss, clipfrac=clipfrac[-1],
                                  elapsed=round(time.time() - started, 1))), flush=True)
    after = digest(vla)
    vla.save_pretrained(output)
    version_id = hashlib.sha256((parent["id"] + after + output.name).encode()).hexdigest()
    receipt = dict(version=dict(id=version_id, location=str(output), parent_id=parent["id"]),
                   operator=operator, optimizer_steps=steps, items=len(episodes),
                   trainable_parameters=sum(p.numel() for p in params),
                   before_sha256=before, after_sha256=after, frames=len(index),
                   seconds=time.time() - started, loss_first=losses[0], loss_last=losses[-1],
                   extra=dict(losses=losses, clipfrac=clipfrac, update=update))
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
