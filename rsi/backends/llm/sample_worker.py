"""vLLM sampling worker: one process per GPU group, requests in, texts out."""

import argparse
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--requests", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--adapter")
    parser.add_argument("--max-lora-rank", type=int, default=64)
    parser.add_argument("--max-model-len", type=int, default=4096)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--tensor-parallel", type=int, default=1)
    parser.add_argument("--trust-remote-code", action="store_true")
    args = parser.parse_args()

    from vllm import LLM, SamplingParams
    rows = [json.loads(line) for line in open(args.requests)]
    llm = LLM(args.model, dtype="bfloat16", max_model_len=args.max_model_len,
              gpu_memory_utilization=args.gpu_memory_utilization,
              tensor_parallel_size=args.tensor_parallel, enable_lora=bool(args.adapter),
              max_lora_rank=args.max_lora_rank, trust_remote_code=args.trust_remote_code,
              seed=0)
    params = [SamplingParams(n=r["n"], temperature=r["temperature"], top_p=r.get("top_p", 1.0),
                             max_tokens=r["max_tokens"], stop=r.get("stop") or None,
                             seed=r.get("seed"), include_stop_str_in_output=True)
              for r in rows]
    lora = None
    if args.adapter:
        from vllm.lora.request import LoRARequest
        lora = LoRARequest("version", 1, args.adapter)
    outputs = llm.generate([r["prompt"] for r in rows], params, lora_request=lora)
    with open(args.out, "w") as stream:
        for row, out in zip(rows, outputs):
            texts = [o.text for o in out.outputs]
            finish = [o.finish_reason for o in out.outputs]
            stream.write(json.dumps(dict(index=row["index"], texts=texts, finish=finish)) + "\n")


if __name__ == "__main__":
    main()
