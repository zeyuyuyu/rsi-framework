"""OpenVLA-OFT x LIBERO rollout worker (runs in the openvla interpreter on one GPU).

Reproduces SimpleVLA-RL's OFT LIBERO rollout (verl/workers/rollout/rob_rollout.py: ``env_worker``,
``process_input``, ``_generate_one_step_oft``): third-person camera only (no wrist image, no
proprio), 180-degree flip, JPEG+lanczos resize to 224, 0.9 center crop, the 29871 spacer token,
one parallel-decoding forward per chunk of 8 actions (56 tokens taken from the last 256 vocabulary
ids, argmax for greedy or softmax(logits / temperature) sampling), un-normalisation with the
``<suite>_no_noops`` q01/q99 statistics, gripper binarise+invert, and every action of the chunk
executed until success or 512 env steps. The model, processor and LIBERO helpers are SimpleVLA-RL's
own code imported from ``openvla_root``; the bidirectional attention their pinned transformers fork
provides is patched into the stock transformers 4.40.1 here (``enable_bidirectional_sdpa``).

Spec JSON and episode fields as the OpenVLA worker. A saved episode holds, per chunk, the cropped
224 frame the policy saw, the 56 tokens it emitted and how many of the chunk's actions ran.
"""

import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

CHUNK, ACTION_DIM = 8, 7
ACTION_TOKENS = 256    # the action bins are the last 256 ids of the 32000-token vocabulary
MAX_STEPS = 512        # RobHFRollout.max_steps, every LIBERO suite
SPACER = 29871
WAIT_STEPS = 10


def decode_chunk(tokens, bin_centers, vocab_size, stats):
    """Action tokens (n, 56) -> un-normalised actions (n, 8, 7), computed as _verl_discrete_prediction
    and _unnormalize_actions (bounds_q99) do; the gripper is left normalised (mask False)."""
    disc = np.clip(vocab_size - np.asarray(tokens) - 1, 0, bin_centers.shape[0] - 1)
    norm = bin_centers[disc].reshape(-1, ACTION_DIM)
    mask = stats.get("mask", np.ones_like(stats["q01"], dtype=bool))
    high, low = np.array(stats["q99"]), np.array(stats["q01"])
    actions = np.where(mask, 0.5 * (norm + 1) * (high - low + 1e-8) + low, norm)
    return actions.reshape(-1, CHUNK, ACTION_DIM)


def run_chunk(step, actions, steps, max_steps):
    """Execute a chunk's actions in order until success or the episode's step budget, as env_worker
    does; returns (last observation, actions executed, success)."""
    obs, n = None, 0
    for action in actions:
        obs, _, done, _ = step(action)
        n += 1
        if done or steps + n >= max_steps:
            return obs, n, bool(done)
    return obs, n, False


def center_crop_image(image):
    """rob_rollout.center_crop_image with its crop_and_resize inlined (crop_scale 0.9, batch 1)."""
    import tensorflow as tf
    from PIL import Image
    crop_scale, batch_size = 0.9, 1
    image = tf.convert_to_tensor(np.array(image))
    orig_dtype = image.dtype
    image = tf.image.convert_image_dtype(image, tf.float32)
    image = tf.expand_dims(image, axis=0)
    new_heights = tf.reshape(tf.clip_by_value(tf.sqrt(crop_scale), 0, 1), shape=(batch_size,))
    new_widths = tf.reshape(tf.clip_by_value(tf.sqrt(crop_scale), 0, 1), shape=(batch_size,))
    height_offsets = (1 - new_heights) / 2
    width_offsets = (1 - new_widths) / 2
    boxes = tf.stack([height_offsets, width_offsets,
                      height_offsets + new_heights, width_offsets + new_widths], axis=1)
    image = tf.image.crop_and_resize(image, boxes, tf.range(batch_size), (224, 224))[0]
    image = tf.clip_by_value(image, 0, 1)
    image = tf.image.convert_image_dtype(image, orig_dtype, saturate=True)
    return Image.fromarray(image.numpy()).convert("RGB")


def enable_bidirectional_sdpa():
    """OpenVLA-OFT pins moojink/transformers-openvla-oft, whose only change to transformers 4.40.1 is
    this hunk of LlamaSdpaAttention.forward: no causal flag, and every query row takes the last row of
    the causal mask (attend to every token except padding). Without it the action chunk is decoded
    causally, unlike training. The rest of the method is stock 4.40.1."""
    import torch
    import transformers
    from transformers.models.llama import modeling_llama as ml
    if transformers.__version__ != "4.40.1":
        raise SystemExit(f"oft_needs_transformers_4.40.1:{transformers.__version__}")

    def forward(self, hidden_states, attention_mask=None, position_ids=None, past_key_value=None,
                output_attentions=False, use_cache=False, cache_position=None):
        if output_attentions:
            raise ValueError("oft_sdpa_without_attention_outputs")
        bsz, q_len, _ = hidden_states.size()
        query_states = self.q_proj(hidden_states)
        key_states = self.k_proj(hidden_states)
        value_states = self.v_proj(hidden_states)
        query_states = query_states.view(bsz, q_len, self.num_heads, self.head_dim).transpose(1, 2)
        key_states = key_states.view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
        value_states = value_states.view(bsz, q_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)
        cos, sin = self.rotary_emb(value_states, position_ids)
        query_states, key_states = ml.apply_rotary_pos_emb(query_states, key_states, cos, sin)
        past_key_value = getattr(self, "past_key_value", past_key_value)
        if past_key_value is not None:
            cache_kwargs = {"sin": sin, "cos": cos, "cache_position": cache_position}
            key_states, value_states = past_key_value.update(key_states, value_states, self.layer_idx, cache_kwargs)
        key_states = ml.repeat_kv(key_states, self.num_key_value_groups)
        value_states = ml.repeat_kv(value_states, self.num_key_value_groups)
        causal_mask = attention_mask
        if attention_mask is not None:
            causal_mask = causal_mask[:, :, :, : key_states.shape[-2]]
        if query_states.device.type == "cuda" and causal_mask is not None:
            query_states = query_states.contiguous()
            key_states = key_states.contiguous()
            value_states = value_states.contiguous()
        if causal_mask is not None:                       # the fork's hunk
            D = causal_mask.shape[-1]
            last_row = causal_mask[:, :, -1, :].clone()
            causal_mask = last_row.unsqueeze(2).expand(-1, -1, D, -1)
        attn_output = torch.nn.functional.scaled_dot_product_attention(
            query_states, key_states, value_states, attn_mask=causal_mask,
            dropout_p=self.attention_dropout if self.training else 0.0, is_causal=False)
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(bsz, q_len, self.hidden_size)
        attn_output = self.o_proj(attn_output)
        return attn_output, None, past_key_value

    ml.LlamaSdpaAttention.forward = forward


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_policy(checkpoint, adapter, root):
    """SimpleVLA-RL's OFT classes loaded directly (the checkpoint ships the original OFT modeling
    files, which their run script overwrites; trust_remote_code would load those), with the config
    overrides of fsdp_workers._build_model_optimizer for LIBERO and one input image."""
    os.environ["ROBOT_PLATFORM"] = "LIBERO"    # constants.py otherwise detects ALOHA chunking
    sys.path.insert(0, str(Path(root) / "verl" / "utils" / "vla_utils"))
    import torch
    from transformers import AutoTokenizer
    from openvla_oft import constants
    from openvla_oft.configuration_prismatic import OpenVLAConfig
    from openvla_oft.modeling_prismatic import OpenVLAForActionPrediction
    from openvla_oft.processing_prismatic import PrismaticImageProcessor, PrismaticProcessor
    if (constants.NUM_ACTIONS_CHUNK, constants.ACTION_DIM) != (CHUNK, ACTION_DIM):
        raise SystemExit("oft_constants_not_libero")
    enable_bidirectional_sdpa()
    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    config = OpenVLAConfig.from_pretrained(checkpoint)
    config.bos_token_id, config.eos_token_id = tokenizer.bos_token_id, tokenizer.eos_token_id
    config.pad_token_id = tokenizer.pad_token_id
    config.use_proprio, config.proprio_dim = False, ACTION_DIM
    vla, info = OpenVLAForActionPrediction.from_pretrained(
        checkpoint, config=config, attn_implementation="sdpa", torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True, output_loading_info=True)
    if info["missing_keys"]:
        raise SystemExit(f"oft_weights_missing:{info['missing_keys'][:5]}")
    if info["unexpected_keys"]:
        print(json.dumps(dict(unused_checkpoint_weights=info["unexpected_keys"])), flush=True)
    if vla.language_model.config._attn_implementation != "sdpa" or vla.vocab_size != 32000:
        raise SystemExit("oft_model_mismatch")
    vla.vision_backbone.set_num_images_in_input(1)
    vla.norm_stats = json.loads((Path(checkpoint) / "dataset_statistics.json").read_text())
    if adapter:
        from peft import PeftModel
        vla = PeftModel.from_pretrained(vla, adapter).merge_and_unload()
    vla = vla.to("cuda:0").eval()
    processor = PrismaticProcessor(PrismaticImageProcessor.from_pretrained(checkpoint), tokenizer)
    return vla, processor


def act(vla, processor, prompt, images, unnorm_key, sample, temperature):
    """One chunk for each image (same prompt): (actions (n, 8, 7), tokens (n, 56))."""
    import torch
    feats = [processor(prompt, image) for image in images]
    ids = torch.cat([f["input_ids"] for f in feats])
    att = torch.cat([f["attention_mask"] for f in feats])
    if not torch.all(ids[:, -1] == SPACER):
        ids = torch.cat([ids, torch.full((ids.shape[0], 1), SPACER, dtype=ids.dtype)], 1)
        att = torch.cat([att, torch.ones((att.shape[0], 1), dtype=att.dtype)], 1)
    pixels = torch.cat([f["pixel_values"] for f in feats]).to("cuda:0")
    with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        actions, tokens = vla.generate_action_verl(
            input_ids=ids.to("cuda:0"), pixel_values=pixels, proprio=None,
            attention_mask=att.to("cuda:0"), padding_idx=processor.tokenizer.pad_token_id,
            do_sample=sample, unnorm_key=unnorm_key, temperature=temperature)
    return actions, tokens.cpu().numpy().astype(np.int64)


def state_sha(env):
    return hashlib.sha256(np.asarray(env.get_sim_state()).tobytes()).hexdigest()[:16]


def main(spec_path):
    spec = json.loads(Path(spec_path).read_text())
    root = Path(spec["openvla_root"])
    import tensorflow as tf
    tf.config.set_visible_devices([], "GPU")
    import torch
    from PIL import Image
    lu = load_module("simplevla_libero_utils", root / "verl" / "utils" / "libero_utils.py")
    from libero.libero import benchmark

    out_dir = Path(spec["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    vla, processor = load_policy(spec["checkpoint"], spec.get("adapter"), root)
    suite_name = spec["suite"]
    unnorm_key = suite_name if suite_name in vla.norm_stats else suite_name + "_no_noops"
    stats = vla.get_action_stats(unnorm_key)
    suite = benchmark.get_benchmark_dict()[suite_name]()
    max_steps = spec.get("max_steps") or MAX_STEPS
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
            env, description = lu.get_libero_env(task, "openvla", resolution=256)
            envs.append(env)
        prompt = f"In: What action should the robot take to {description.lower()}?\nOut:"
        for b in range(0, len(eps), n_envs):
            batch = eps[b:b + n_envs]
            obs, init_sha = [], []
            for env, ep in zip(envs, batch):
                init = ep["init"]
                # Re-seed per episode so an episode's outcome does not depend on how many
                # episodes this env object ran before it (LIBERO's env RNG advances on reset).
                seed = 0 if init["kind"] == "official" else init["seed"]
                np.random.seed(seed)
                env.seed(seed)
                o = env.reset()
                if init["kind"] == "official":
                    o = env.set_init_state(init_states[init["index"]])
                init_sha.append(state_sha(env))
                for _ in range(WAIT_STEPS):
                    o, _, _, _ = env.step(lu.get_libero_dummy_action("openvla"))
                obs.append(o)
            n = len(batch)
            done, success, steps = [False] * n, [False] * n, [0] * n
            frames, tokens, executed = [[] for _ in range(n)], [[] for _ in range(n)], [[] for _ in range(n)]
            if mode == "sample":
                torch.manual_seed(batch[0]["sample_seed"])
            while not all(done):
                active = [i for i in range(n) if not done[i]]
                imgs = [center_crop_image(Image.fromarray(lu.get_libero_image(obs[i], 224)).convert("RGB"))
                        for i in active]
                acts, toks = act(vla, processor, prompt, imgs, unnorm_key, mode == "sample", float(temperature))
                if not np.allclose(decode_chunk(toks, vla.bin_centers, vla.vocab_size, stats), acts,
                                   rtol=0, atol=1e-9):
                    raise SystemExit("decode_chunk_disagrees_with_reference")
                for j, i in enumerate(active):
                    env = envs[i]
                    step = lambda a, env=env: env.step(
                        lu.invert_gripper_action(lu.normalize_gripper_action(a, binarize=True)).tolist())
                    o, k, ok = run_chunk(step, acts[j], steps[i], max_steps)
                    obs[i] = o
                    steps[i] += k
                    if batch[i]["save"]:
                        frames[i].append(np.asarray(imgs[j], np.uint8))
                        tokens[i].append(toks[j])
                        executed[i].append(k)
                    if ok or steps[i] >= max_steps:
                        done[i], success[i] = True, ok
            for i, ep in enumerate(batch):
                path = None
                if ep["save"]:
                    path = str(out_dir / f"{ep['id']}.npz")
                    np.savez_compressed(path, frames=np.asarray(frames[i], np.uint8),
                                        tokens=np.asarray(tokens[i], np.int64),
                                        executed=np.asarray(executed[i], np.int64),
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
