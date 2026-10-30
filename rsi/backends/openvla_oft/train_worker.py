"""OpenVLA-OFT LoRA worker. Operators: ``bc`` and ``grpo`` over the policy's own episodes.

A training unit is one chunk: the frame the policy saw and the 56 tokens it emitted, of which only
the tokens of actions that ran count (SimpleVLA-RL masks tokens past ``finish_step`` the same way).
Log-probs are taken as SimpleVLA-RL's actor takes them (dp_rob.py): the model's parallel-decoding
forward, logits restricted to the 256 action-token ids, divided by the rollout temperature.

bc   - items {episode}; NLL of the emitted chunk tokens (temperature 1).
grpo - items {experience: {episode, temperature}, advantage}; the episode-level advantage applies
       to every counted token; token-level PPO-clip against the parent policy (old log-probs
       computed here before the first update), logits scaled by the rollout temperature so the
       ratio is taken against the behaviour policy; no KL.
Losses are means over the counted tokens of each optimizer batch; the LoRA recipe, adapter and
receipt follow the OpenVLA train worker.
"""

import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

CHUNK, ACTION_DIM, ACTION_TOKENS = 8, 7, 256
FIRST_ACTION_ID = 32000 - ACTION_TOKENS    # load_policy checks the 32000-token vocabulary


def token_mask(executed, chunk=CHUNK, action_dim=ACTION_DIM):
    """Actions executed per chunk (n,) -> (n, chunk * action_dim) mask of the tokens whose action ran."""
    ran = np.arange(chunk)[None, :] < np.asarray(executed)[:, None]
    return np.repeat(ran, action_dim, axis=1)


def action_logits(model, processor, prompt, frames):
    """(len(frames), 56, 256) logits over the action ids at the chunk positions, from the OFT forward the
    SimpleVLA-RL actor trains (dp_rob._forward_micro_batch_update). The forward reads the prompt length
    off the batch, so all frames share one prompt (no padding)."""
    import torch
    from PIL import Image
    ids = torch.tensor([list(prompt)] * len(frames), device="cuda:0")
    pixels = torch.stack([processor.image_processor.apply_transform(Image.fromarray(f).convert("RGB"))
                          for f in frames]).to("cuda:0")
    with torch.autocast("cuda", dtype=torch.bfloat16):
        logits = model(input_ids=ids, attention_mask=torch.ones_like(ids), pixel_values=pixels)
    return logits[..., FIRST_ACTION_ID:FIRST_ACTION_ID + ACTION_TOKENS].float()


def digest(model):
    h = hashlib.sha256()
    for name, p in model.named_parameters():
        if p.requires_grad:
            h.update(name.encode())
            h.update(p.detach().float().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def main(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import torch
    from peft import LoraConfig, PeftModel, get_peft_model
    from rollout_worker import SPACER, load_policy

    update = spec["update"]
    operator = update["operator"]
    torch.manual_seed(spec["seed"])
    rng = random.Random(spec["seed"])
    output = Path(spec["output"])
    output.mkdir(parents=True, exist_ok=False)
    vla, processor = load_policy(spec["checkpoint"], None, spec["openvla_root"])
    tok = processor.tokenizer

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
        episodes.append(dict(frames=data["frames"], tokens=data["tokens"], mask=token_mask(data["executed"]),
                             prompt=ids, adv=adv,
                             temperature=float(exp.get("temperature") or 1.0) or 1.0))
    index = [(e, c) for e in range(len(episodes)) for c in range(len(episodes[e]["tokens"]))]
    if not index:
        raise SystemExit("no_training_frames")

    def chunk_logprobs(model, picks):
        """(len(picks), 56) log-probs of the emitted tokens; picks run in groups sharing a prompt."""
        groups = {}
        for k, (e, c) in enumerate(picks):
            groups.setdefault(tuple(episodes[e]["prompt"]), []).append(k)
        rows = [None] * len(picks)
        for prompt, ks in groups.items():
            logits = action_logits(model, processor, prompt,
                                   [episodes[picks[k][0]]["frames"][picks[k][1]] for k in ks])
            temps = torch.tensor([episodes[picks[k][0]]["temperature"] if operator == "grpo" else 1.0
                                  for k in ks], device=logits.device)[:, None, None]
            target = torch.tensor(np.stack([episodes[picks[k][0]]["tokens"][picks[k][1]] for k in ks]),
                                  device=logits.device) - FIRST_ACTION_ID
            lp = torch.log_softmax(logits / temps, -1).gather(-1, target.unsqueeze(-1)).squeeze(-1)
            for j, k in enumerate(ks):
                rows[k] = lp[j]
        return torch.stack(rows)

    def masks(picks):
        return torch.tensor(np.stack([episodes[e]["mask"][c] for e, c in picks]), device="cuda:0")

    parent = spec["parent"]
    if parent["parent_id"] is None:
        vla = get_peft_model(vla, LoraConfig(r=spec["lora_rank"], lora_alpha=spec["lora_alpha"],
                                             lora_dropout=0.0, target_modules=spec["target_modules"],
                                             init_lora_weights="gaussian"))
    else:
        vla = PeftModel.from_pretrained(vla, parent["location"], is_trainable=True)
    mb = spec["micro_batch"]
    steps, batch = int(update["steps"]), int(update["batch"])
    schedule, order, cursor = [], [], 0
    for step in range(steps):
        picks = []
        while len(picks) < batch:
            if cursor >= len(order):
                order, cursor = list(range(len(index))), 0
                rng.shuffle(order)
            picks.append(index[order[cursor]])
            cursor += 1
        schedule.append(picks)
    # "legacy": old log-probs from one pass over the frames in episode order. Under bf16 a frame's log-probs
    # depend on which frames share its forward, so ~5% of tokens left the clip band before any update (A800
    # pilot-4 replica, step 1). "matched": old log-probs from the exact micro-batches training will run, so
    # the ratio starts at 1 and only the update moves it.
    ratio_mode = update.get("ratio", "legacy")
    # "token" (default): every counted token weighs the same, so episodes that run to the step limit (failures,
    # 2-3x the chunks of a success) carry most of the gradient. "episode": each chunk weighs 1 / (chunks of its
    # episode), so every episode carries the same total weight, as in GRPO's per-sequence mean.
    loss_agg = update.get("loss_agg", "token")
    if loss_agg not in ("token", "episode"):
        raise SystemExit(f"unknown_loss_agg:{loss_agg}")

    def chunk_weights(picks):
        if loss_agg == "token":
            return torch.ones(len(picks), 1, device="cuda:0")
        return torch.tensor([1.0 / len(episodes[e]["tokens"]) for e, _ in picks], device="cuda:0")[:, None]
    old = None
    if operator == "grpo" and ratio_mode == "legacy":
        vla.eval()
        old = {}
        with torch.no_grad():
            for b in range(0, len(index), mb):
                picks = index[b:b + mb]
                lp = chunk_logprobs(vla, picks)
                for k, key in enumerate(picks):
                    old[key] = lp[k].detach()
    elif operator == "grpo" and ratio_mode == "matched":
        vla.train()
        old = {}
        with torch.no_grad():
            for step, picks in enumerate(schedule):
                for b in range(0, batch, mb):
                    old[(step, b)] = chunk_logprobs(vla, picks[b:b + mb]).detach()
    elif operator == "grpo":
        raise SystemExit(f"unknown_ratio_mode:{ratio_mode}")
    vla.train()
    params = [p for p in vla.parameters() if p.requires_grad]
    before = digest(vla)
    opt = torch.optim.AdamW(params, lr=float(update["lr"]), weight_decay=0.0)
    clip_lo, clip_hi = float(update.get("clip_low", 0.2)), float(update.get("clip_high", 0.28))
    losses, clipfrac, step1_logratio = [], [], None
    started = time.time()
    for step, picks in enumerate(schedule):
        counted = float(masks(picks).sum())
        weighted = float((masks(picks) * chunk_weights(picks)).sum())
        opt.zero_grad(set_to_none=True)
        step_loss, clipped = 0.0, 0
        for b in range(0, batch, mb):
            chunk = picks[b:b + mb]
            m = masks(chunk)
            lp = chunk_logprobs(vla, chunk)
            if operator == "bc":
                obj = lp
            else:
                ref = old[(step, b)] if ratio_mode == "matched" else torch.stack([old[k] for k in chunk])
                ratio = torch.exp(lp - ref)
                adv = torch.tensor([episodes[e]["adv"] for e, _ in chunk], device=lp.device)[:, None]
                obj = torch.min(ratio * adv, torch.clamp(ratio, 1 - clip_lo, 1 + clip_hi) * adv)
                clipped += int((((ratio < 1 - clip_lo) | (ratio > 1 + clip_hi)) & m).sum())
                if step == 0:
                    dev = (lp - ref).detach()[m]
                    step1_logratio = (step1_logratio or []) + dev.cpu().tolist()
            loss = -(torch.where(m, obj, torch.zeros_like(obj)) * chunk_weights(chunk)).sum() / weighted
            if not torch.isfinite(loss):
                raise SystemExit("nonfinite_loss")
            loss.backward()
            step_loss += float(loss)
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        losses.append(step_loss)
        clipfrac.append(clipped / counted if operator == "grpo" else 0.0)
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
                   extra=dict(losses=losses, clipfrac=clipfrac, update=update, ratio_mode=ratio_mode, loss_agg=loss_agg,
                              step1_logratio=None if not step1_logratio else dict(
                                  mean_abs=float(np.mean(np.abs(step1_logratio))),
                                  max_abs=float(np.max(np.abs(step1_logratio))),
                                  outside_clip=float(np.mean((np.array(step1_logratio) < np.log(1 - clip_lo))
                                                             | (np.array(step1_logratio) > np.log(1 + clip_hi))))),
                              counted_tokens=int(sum(int(episodes[e]["mask"][c].sum()) for e, c in index))))
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
