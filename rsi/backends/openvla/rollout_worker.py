"""OpenVLA x LIBERO rollout worker (runs in the openvla interpreter on one GPU).

Batches up to ``n_envs`` concurrent episodes of the same task and mode into one
generate call. Preprocessing and decoding replicate OpenVLA's
``get_vla_action`` / ``predict_action`` (180-degree flip, JPEG+lanczos resize to
224, 0.9 center crop, the 29871 spacer token, bin-centre decoding and
un-normalisation, gripper binarise+invert). The batch>1 guards in the prismatic
wrapper are bypassed the same way the earlier, equivalence-checked quality study
did (experiments/correction/quality/qlib.py): episodes in one batch share the
prompt, so no padding is involved.

Spec JSON: checkpoint, adapter|null, suite, max_steps, n_envs, out_dir, episodes.
Each episode: id, case_id, task_id, init{kind: official|random, index|seed},
mode greedy|sample, temperature, sample_seed, save.
"""

import hashlib
import json
import os
import sys
import time
import types
from pathlib import Path

import numpy as np

MAX_STEPS = {"libero_spatial": 220, "libero_object": 280, "libero_goal": 300,
             "libero_10": 520, "libero_90": 400}
SPACER = 29871
WAIT_STEPS = 10


def enable_batched_generation(model):
    from prismatic.extern.hf.modeling_prismatic import PrismaticCausalLMOutputWithPast

    def prep(self, input_ids=None, past_key_values=None, inputs_embeds=None,
             pixel_values=None, attention_mask=None, **kwargs):
        if past_key_values is not None:
            input_ids = input_ids[:, -1:]
        inputs = ({"input_embeds": inputs_embeds}
                  if inputs_embeds is not None and past_key_values is None
                  else {"input_ids": input_ids})
        inputs.update(attention_mask=attention_mask, pixel_values=pixel_values,
                      past_key_values=past_key_values, use_cache=kwargs.get("use_cache"))
        return inputs

    original = model.forward

    def forward(self, input_ids=None, attention_mask=None, pixel_values=None,
                past_key_values=None, use_cache=None, labels=None, inputs_embeds=None,
                output_attentions=None, output_hidden_states=None,
                output_projector_features=None, return_dict=None, **kw):
        if (input_ids is not None and input_ids.shape[1] == 1 and input_ids.shape[0] > 1
                and past_key_values is not None):
            lm = self.language_model(input_ids=input_ids, attention_mask=None,
                                     position_ids=None, past_key_values=past_key_values,
                                     inputs_embeds=None, labels=None, use_cache=use_cache,
                                     output_attentions=output_attentions,
                                     output_hidden_states=output_hidden_states,
                                     return_dict=True)
            return PrismaticCausalLMOutputWithPast(
                loss=lm.loss, logits=lm.logits, past_key_values=lm.past_key_values,
                hidden_states=lm.hidden_states, attentions=lm.attentions,
                projector_features=None)
        return original(input_ids=input_ids, attention_mask=attention_mask,
                        pixel_values=pixel_values, past_key_values=past_key_values,
                        use_cache=use_cache, labels=labels, inputs_embeds=inputs_embeds,
                        output_attentions=output_attentions,
                        output_hidden_states=output_hidden_states,
                        output_projector_features=output_projector_features,
                        return_dict=return_dict, **kw)

    model.prepare_inputs_for_generation = types.MethodType(prep, model)
    model.forward = types.MethodType(forward, model)
    return model


def load_policy(checkpoint, adapter):
    import torch
    from transformers import (AutoConfig, AutoImageProcessor, AutoModelForVision2Seq,
                              AutoProcessor)
    from prismatic.extern.hf.configuration_prismatic import OpenVLAConfig
    from prismatic.extern.hf.modeling_prismatic import OpenVLAForActionPrediction
    from prismatic.extern.hf.processing_prismatic import (PrismaticImageProcessor,
                                                          PrismaticProcessor)
    AutoConfig.register("openvla", OpenVLAConfig)
    AutoImageProcessor.register(OpenVLAConfig, PrismaticImageProcessor)
    AutoProcessor.register(OpenVLAConfig, PrismaticProcessor)
    AutoModelForVision2Seq.register(OpenVLAConfig, OpenVLAForActionPrediction)
    vla = AutoModelForVision2Seq.from_pretrained(
        checkpoint, attn_implementation="sdpa", torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True, trust_remote_code=True)
    stats = Path(checkpoint) / "dataset_statistics.json"
    if stats.exists():
        vla.norm_stats = json.loads(stats.read_text())
    if adapter:
        from peft import PeftModel
        vla = PeftModel.from_pretrained(vla, adapter).merge_and_unload()
    vla = vla.to("cuda:0").eval()
    enable_batched_generation(vla)
    processor = AutoProcessor.from_pretrained(checkpoint, trust_remote_code=True)
    return vla, processor


def crop_batch(images):
    """Per-image 0.9 center crop, exactly as get_vla_action does for batch size 1."""
    import tensorflow as tf
    from experiments.robot.openvla_utils import crop_and_resize
    out = []
    for image in images:
        t = tf.image.convert_image_dtype(tf.convert_to_tensor(image), tf.float32)
        t = tf.clip_by_value(crop_and_resize(t, 0.9, 1), 0, 1)
        out.append(tf.image.convert_image_dtype(t, tf.uint8, saturate=True).numpy())
    return out


def decode(vla, tokens, unnorm_key):
    disc = vla.vocab_size - tokens
    disc = np.clip(disc - 1, 0, vla.bin_centers.shape[0] - 1)
    norm = vla.bin_centers[disc]
    s = vla.get_action_stats(unnorm_key)
    mask = s.get("mask", np.ones_like(s["q01"], dtype=bool))
    high, low = np.array(s["q99"]), np.array(s["q01"])
    actions = np.where(mask, 0.5 * (norm + 1) * (high - low) + low, norm).astype(np.float32)
    actions[..., -1] = 2 * actions[..., -1] - 1          # normalize_gripper_action
    actions[..., -1] = np.sign(actions[..., -1])         # binarize=True
    actions[..., -1] = -actions[..., -1]                 # invert_gripper_action
    return actions


def state_sha(env):
    return hashlib.sha256(np.asarray(env.get_sim_state()).tobytes()).hexdigest()[:16]


def main(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    sys.path.append(spec["openvla_root"])
    import tensorflow as tf
    tf.config.set_visible_devices([], "GPU")
    import torch
    from experiments.robot.libero.libero_utils import (get_libero_dummy_action,
                                                       get_libero_env, get_libero_image)
    from libero.libero import benchmark

    out_dir = Path(spec["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    vla, processor = load_policy(spec["checkpoint"], spec.get("adapter"))
    suite_name = spec["suite"]
    unnorm_key = suite_name if suite_name in vla.norm_stats else suite_name + "_no_noops"
    adim = vla.get_action_dim(unnorm_key)
    suite = benchmark.get_benchmark_dict()[suite_name]()
    max_steps = spec.get("max_steps") or MAX_STEPS[suite_name]
    n_envs = spec["n_envs"]
    results = open(out_dir / f"results-{os.getpid()}.jsonl", "a")
    groups = {}
    for ep in spec["episodes"]:
        groups.setdefault((ep["task_id"], ep["mode"], ep["temperature"]), []).append(ep)
    started = time.time()
    for (task_id, mode, temperature), eps in sorted(groups.items()):
        task = suite.get_task(task_id)
        init_states = suite.get_task_init_states(task_id)
        envs, description = [], None
        for _ in range(min(n_envs, len(eps))):
            env, description = get_libero_env(task, "openvla", resolution=256)
            envs.append(env)
        prompt = f"In: What action should the robot take to {description.lower()}?\nOut:"
        for b in range(0, len(eps), n_envs):
            batch = eps[b:b + n_envs]
            obs, init_sha = [], []
            for env, ep in zip(envs, batch):
                init = ep["init"]
                env.reset()
                if init["kind"] == "official":
                    o = env.set_init_state(init_states[init["index"]])
                else:
                    np.random.seed(init["seed"])
                    env.seed(init["seed"])
                    o = env.reset()
                init_sha.append(state_sha(env))
                for _ in range(WAIT_STEPS):
                    o, _, _, _ = env.step(get_libero_dummy_action("openvla"))
                obs.append(o)
            n = len(batch)
            done = [False] * n
            success = [False] * n
            steps = [0] * n
            frames = [[] for _ in range(n)]
            tokens = [[] for _ in range(n)]
            if mode == "sample":
                torch.manual_seed(batch[0]["sample_seed"])
            for t in range(max_steps):
                active = [i for i in range(n) if not done[i]]
                if not active:
                    break
                imgs = crop_batch([get_libero_image(obs[i], 224) for i in active])
                from PIL import Image
                pil = [Image.fromarray(im).convert("RGB") for im in imgs]
                inputs = processor([prompt] * len(active), pil, return_tensors="pt")
                ids = inputs["input_ids"].to("cuda:0")
                att = inputs["attention_mask"].to("cuda:0")
                if not torch.all(ids[:, -1] == SPACER):
                    ids = torch.cat([ids, torch.full((ids.shape[0], 1), SPACER,
                                                     dtype=ids.dtype, device=ids.device)], 1)
                    att = torch.cat([att, torch.ones((att.shape[0], 1), dtype=att.dtype,
                                                     device=att.device)], 1)
                pv = inputs["pixel_values"].to("cuda:0", dtype=torch.bfloat16)
                kw = (dict(do_sample=True, temperature=float(temperature))
                      if mode == "sample" else dict(do_sample=False))
                with torch.inference_mode():
                    gen = vla.generate(ids, attention_mask=att, pixel_values=pv,
                                       max_new_tokens=adim, **kw)
                toks = gen[:, -adim:].cpu().numpy().astype(np.int64)
                acts = decode(vla, toks, unnorm_key)
                for j, i in enumerate(active):
                    if batch[i]["save"]:
                        frames[i].append(imgs[j])
                        tokens[i].append(toks[j])
                    o, _, d, _ = envs[i].step(acts[j].tolist())
                    obs[i] = o
                    steps[i] = t + 1
                    if d:
                        done[i] = success[i] = True
            for i, ep in enumerate(batch):
                path = None
                if ep["save"]:
                    path = str(out_dir / f"{ep['id']}.npz")
                    np.savez_compressed(path, frames=np.asarray(frames[i], np.uint8),
                                        tokens=np.asarray(tokens[i], np.int64),
                                        task=description, success=success[i],
                                        task_id=task_id, mode=mode)
                results.write(json.dumps(dict(
                    id=ep["id"], case_id=ep["case_id"], task_id=task_id, init=ep["init"],
                    mode=mode, temperature=temperature, success=success[i], steps=steps[i],
                    path=path, init_state_sha=init_sha[i],
                    elapsed=round(time.time() - started, 1))) + "\n")
                results.flush()
        for env in envs:
            env.close()
    results.close()


if __name__ == "__main__":
    main(sys.argv[1])
