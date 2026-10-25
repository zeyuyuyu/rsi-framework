"""LoRA training worker for causal LMs. Operators: ``sft`` and ``grpo``.

sft  - items {prompt, completion}; next-token loss on completion tokens.
grpo - items {experience: {prompt, completion}, advantage}; token-level
       PPO-clip policy gradient against the *parent* policy (old log-probs are
       computed here, before the first update, by the same model code), no KL,
       zero-advantage items skipped, asymmetric clip (clip_low, clip_high).
Both inherit the parent adapter, never truncate silently, and write a receipt
binding parent, items, steps and trainable-parameter digests.
"""

import hashlib
import json
import math
import random
import shutil
import sys
import time
from pathlib import Path


def digest(model):
    h = hashlib.sha256()
    for name, p in model.named_parameters():
        if p.requires_grad:
            h.update(name.encode())
            h.update(p.detach().float().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def batches(records, size, rng):
    order, cursor = [], 0
    while True:
        out = []
        while len(out) < size:
            if cursor >= len(order):
                order, cursor = list(range(len(records))), 0
                rng.shuffle(order)
            out.append(order[cursor])
            cursor += 1
        yield out


def pad(torch, rows, pad_id):
    width = max(len(ids) for ids, _ in rows)
    ids = torch.full((len(rows), width), pad_id, dtype=torch.long)
    att = torch.zeros((len(rows), width), dtype=torch.long)
    for i, (x, _) in enumerate(rows):
        ids[i, :len(x)] = torch.tensor(x)
        att[i, :len(x)] = 1
    return ids, att


def token_logprobs(torch, model, ids, att, starts, lengths):
    """Per-row log-probs of tokens ids[start:start+length] (the completion)."""
    out = model(input_ids=ids, attention_mask=att).logits.float()
    logp = torch.log_softmax(out[:, :-1], dim=-1)
    target = ids[:, 1:]
    picked = logp.gather(-1, target.unsqueeze(-1)).squeeze(-1)
    return [picked[i, s - 1:s - 1 + n] for i, (s, n) in enumerate(zip(starts, lengths))]


def main(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    import torch
    from peft import LoraConfig, PeftModel, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    update = spec["update"]
    operator = update["operator"]
    torch.manual_seed(spec["seed"])
    rng = random.Random(spec["seed"])
    output = Path(spec["output"])
    output.mkdir(parents=True, exist_ok=False)
    tok = AutoTokenizer.from_pretrained(spec["base_path"], local_files_only=True)
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    model = AutoModelForCausalLM.from_pretrained(
        spec["base_path"], local_files_only=True, torch_dtype=torch.bfloat16,
        device_map="auto" if spec["multi_gpu_device_map"] else {"": 0})
    model.config.use_cache = False
    parent = spec["parent"]
    if parent["parent_id"] is None:
        model = get_peft_model(model, LoraConfig(
            r=spec["lora_rank"], lora_alpha=spec["lora_alpha"], lora_dropout=0.0,
            target_modules=spec["target_modules"], task_type="CAUSAL_LM"))
    else:
        model = PeftModel.from_pretrained(model, parent["location"], is_trainable=True)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    dev = next(p.device for p in model.parameters())

    items = [json.loads(line) for line in open(spec["items"])]
    records, skipped = [], 0
    for item in items:
        exp = item if operator == "sft" else item["experience"]
        adv = 1.0 if operator == "sft" else float(item["advantage"])
        if operator == "grpo" and adv == 0.0:
            continue
        p = tok(exp["prompt"], add_special_tokens=True)["input_ids"]
        c = tok(exp["completion"], add_special_tokens=False)["input_ids"] + [tok.eos_token_id]
        if len(p) + len(c) > spec["max_seq_len"]:
            skipped += 1
            continue
        records.append(dict(ids=p + c, start=len(p), length=len(c), adv=adv))
    if not records:
        raise SystemExit("no_trainable_items")
    mb = spec["micro_batch"]

    old = None
    if operator == "grpo":
        model.eval()
        old = [None] * len(records)
        with torch.no_grad():
            for b in range(0, len(records), mb):
                chunk = records[b:b + mb]
                ids, att = pad(torch, [(r["ids"], None) for r in chunk], pad_id)
                lps = token_logprobs(torch, model, ids.to(dev), att.to(dev),
                                     [r["start"] for r in chunk], [r["length"] for r in chunk])
                for k, lp in enumerate(lps):
                    old[b + k] = lp.detach()
        model.train()

    params = [p for p in model.parameters() if p.requires_grad]
    before = digest(model)
    opt = torch.optim.AdamW(params, lr=float(update["lr"]), weight_decay=0.0)
    warm = int(update.get("warmup", 5 if operator == "sft" else 0))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / max(1, warm)))
    steps, batch = int(update["steps"]), int(update["batch"])
    clip_lo, clip_hi = float(update.get("clip_low", 0.2)), float(update.get("clip_high", 0.28))
    losses, clipfrac = [], []
    started = time.time()
    model.train()
    stream = batches(records, batch, rng)
    for step in range(steps):
        picks = next(stream)
        opt.zero_grad(set_to_none=True)
        total_tokens = sum(records[i]["length"] for i in picks)
        step_loss, clipped, counted = 0.0, 0, 0
        for b in range(0, len(picks), mb):
            chunk = [records[i] for i in picks[b:b + mb]]
            ids, att = pad(torch, [(r["ids"], None) for r in chunk], pad_id)
            lps = token_logprobs(torch, model, ids.to(dev), att.to(dev),
                                 [r["start"] for r in chunk], [r["length"] for r in chunk])
            loss = 0.0
            for k, (r, lp) in enumerate(zip(chunk, lps)):
                if operator == "sft":
                    loss = loss - lp.sum()
                else:
                    ratio = torch.exp(lp - old[picks[b + k]])
                    a = r["adv"]
                    unclipped = ratio * a
                    clipped_obj = torch.clamp(ratio, 1 - clip_lo, 1 + clip_hi) * a
                    loss = loss - torch.min(unclipped, clipped_obj).sum()
                    clipped += int(((ratio < 1 - clip_lo) | (ratio > 1 + clip_hi)).sum())
                    counted += r["length"]
            loss = loss / total_tokens
            if not torch.isfinite(loss):
                raise SystemExit("nonfinite_loss")
            loss.backward()
            step_loss += float(loss)
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        sched.step()
        losses.append(step_loss)
        clipfrac.append(clipped / counted if counted else 0.0)
        print(json.dumps(dict(step=step + 1, loss=step_loss, clipfrac=clipfrac[-1],
                              elapsed=round(time.time() - started, 1))), flush=True)
    after = digest(model)
    model.save_pretrained(output, safe_serialization=True)
    trainable = sum(p.numel() for p in params)
    merged = model.merge_and_unload()
    merged.save_pretrained(output / "merged", safe_serialization=True)
    tok.save_pretrained(output / "merged")
    src = Path(spec["base_path"]) / "generation_config.json"
    if src.exists():
        shutil.copy(src, output / "merged" / "generation_config.json")
    version_id = hashlib.sha256((parent["id"] + after + output.name).encode()).hexdigest()
    receipt = dict(version=dict(id=version_id, location=str(output), parent_id=parent["id"]),
                   operator=operator, optimizer_steps=steps, items=len(records),
                   trainable_parameters=trainable, before_sha256=before, after_sha256=after,
                   skipped_too_long=skipped, seconds=time.time() - started,
                   loss_first=losses[0], loss_last=losses[-1],
                   extra=dict(losses=losses, clipfrac=clipfrac, update=update,
                              item_digest=hashlib.sha256(
                                  open(spec["items"], "rb").read()).hexdigest()))
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
