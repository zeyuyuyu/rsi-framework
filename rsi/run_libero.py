"""Run the two-level RSI loop on a VLA policy in LIBERO from a frozen plan.

    python -m rsi.run_libero --plan plan.json --out runs/<new-dir> [--baseline-only --replicates N]
                                                                  [--heldout-eval receipt.json]
                                                                  [--test-eval runs/<ended-run> --replicates N]
                                                                  [--resume]   (continue runs/<dir> in place)

Plan keys: model_name, vla (VLAConfig fields + model_family: openvla | oft, default openvla),
suite, tasks, heldout_per_task,
test_inits_per_task, program (overrides), engine (EngineConfig fields), budget_scale (onebig),
meta {proposer: fixed|numeric|llm|llm3 (+ base_url, model, key_file, max_calls; llm3: memory, memory_sha256)}.
"""

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path

from .core.gpu import stop_workers_on_sigterm
from .backends.openvla.backend import VLABackend, VLAConfig
from .backends.openvla_oft.backend import OFTBackend
from .core.engine import Engine, EngineConfig
from .core.types import Version
from .domains.libero.domain import LiberoDomain
from .meta.proposers import FixedProgram, LLMMetaProposer, NumericSearch, OpenAICompatClient
from .meta.relay import RelayClient

BACKENDS = {"openvla": VLABackend, "oft": OFTBackend}


def make_backend(vcfg):
    """The plan's ``vla`` section (tuples already converted) -> backend for its model family."""
    vcfg = dict(vcfg)
    family = vcfg.pop("model_family", "openvla")
    if family not in BACKENDS:
        raise SystemExit(f"unknown_model_family:{family}")
    return BACKENDS[family](VLAConfig(**vcfg))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("--replicates", type=int, default=1)
    # gate + audit only (never the test suite) for a version given by its training receipt, e.g. a
    # pilot candidate whose in-run evaluation failed
    parser.add_argument("--heldout-eval", metavar="RECEIPT")
    # further test replicates of an ended run's retained version (VLA addendum 2: single 500-episode
    # evaluations of one model differ by up to 3.6 points, so a final is averaged over replicates)
    parser.add_argument("--test-eval", metavar="RUN_DIR")
    # with --test-eval: score this node of the run instead of the retained one (its ckpt-<node> must exist)
    parser.add_argument("--node")
    # continue an interrupted run in place (Engine.run(resume=True); the stored plan must match)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    stop_workers_on_sigterm()
    plan = json.loads(Path(args.plan).read_text())
    out = Path(args.out)
    if args.resume and not (out / "plan.json").exists():
        raise SystemExit("resume_needs_an_existing_run")
    if out.exists() and not args.resume:
        raise SystemExit("fresh_output_required")
    vcfg = dict(plan["vla"])
    for key in ("rollout_gpus", "train_gpus", "target_modules"):
        if key in vcfg:
            vcfg[key] = tuple(vcfg[key])
    vcfg.setdefault("workdir", str(out) + ".work")
    backend = make_backend(vcfg)
    domain = LiberoDomain(plan["suite"], plan["tasks"], plan.get("budget_scale", 1),
                          v2=bool(plan.get("engine", {}).get("meta_v2")))
    test = domain.official_test(plan.get("test_inits_per_task", 50))
    initial = Version(f"base:{plan['model_name']}", vcfg["checkpoint"], None)
    if args.baseline_only:
        out.mkdir(parents=True)
        scores = []
        for rep in range(args.replicates):
            records = domain.evaluate(backend, initial, test)
            scores.append(sum(r.score for r in records) / len(records))
            with (out / f"baseline-rep{rep}.jsonl").open("w") as s:
                for r in records:
                    s.write(json.dumps(asdict(r)) + "\n")
        (out / "baseline.json").write_text(json.dumps(dict(model=plan["model_name"],
                                                           test_success=scores), indent=2))
        print(json.dumps(scores))
        return
    if args.heldout_eval:
        version = Version(**json.loads(Path(args.heldout_eval).read_text())["version"])
        gate, audit = domain.heldout(plan["heldout_per_task"])
        out.mkdir(parents=True)
        scores = {}
        for split, cases in (("gate", gate), ("audit", audit)):
            records = domain.evaluate(backend, version, cases)
            scores[split] = sum(r.score for r in records) / len(records)
            with (out / f"{split}-{version.id[:12]}.jsonl").open("w") as s:
                for r in records:
                    s.write(json.dumps(asdict(r)) + "\n")
        (out / "heldout_eval.json").write_text(json.dumps(dict(version=asdict(version), **scores), indent=2))
        print(json.dumps(scores))
        return
    if args.test_eval:
        run = Path(args.test_eval)
        report = json.loads((run / "report.json").read_text())   # written only when the run has ended
        node = args.node or report["retained"]                   # --node: addendum 18 am. 1 (R5-ungated)
        version = initial if node == "n0" else \
            Version(**json.loads((run / f"ckpt-{node}" / "receipt.json").read_text())["version"])
        out.mkdir(parents=True)
        scores = []
        for rep in range(1, args.replicates + 1):    # rep 0 is the run's own test
            records = domain.evaluate(backend, version, test)
            scores.append(sum(r.score for r in records) / len(records))
            with (out / f"test-libero_official-{node}-rep{rep}.jsonl").open("w") as s:
                for r in records:
                    s.write(json.dumps(asdict(r)) + "\n")
        (out / "test_eval.json").write_text(json.dumps(dict(run=str(run), node=node, version=asdict(version),
                                                            test_success=scores), indent=2))
        print(json.dumps(scores))
        return
    program = domain.default_program()
    for section, values in (plan.get("program") or {}).items():
        program[section].update(values)
    gate, audit = domain.heldout(plan["heldout_per_task"])
    kind = plan.get("meta", {}).get("proposer", "fixed")
    meta_space = plan.get("meta", {}).get("space")
    harness = meta_space in ("harness", "v2")                    # addendum 16: knobs + harness components
    space = domain.harness_space if harness else domain.edit_space
    doc = domain.harness_doc if harness else ""
    if meta_space == "v2":                                      # addendum 21: + per-task allocation weights
        assert domain.v2, "meta space v2 needs engine.meta_v2 = true"
        space, doc = domain.v2_space, domain.v2_doc
    validate = domain.validate_program
    if plan.get("meta", {}).get("budget") == "seed":            # addendum 19: no proposal may out-spend the seed
        doc = (doc + "\n" + domain.set_budget_cap(program)).strip()
        validate = domain.validate_capped
    if kind == "fixed":
        proposer = FixedProgram()
    elif kind == "numeric":
        proposer = NumericSearch(space, validate, domain.coupling)
    elif kind == "replica":             # addendum 21: compute-matched fixed control (engine.replica_candidates)
        assert plan.get("engine", {}).get("replica_candidates"), "proposer replica needs engine.replica_candidates"
        proposer = FixedProgram()
    elif kind == "llm":                 # addendum 14: an external LLM diagnoses the round history and edits the program
        m = plan["meta"]          # the log lands in the run dir, which the engine creates before any proposal
        # the numeric fallback never edits task_weights (it cannot mutate a list); v2 keeps it on the harness space
        proposer = LLMMetaProposer(space, validate,
                                   NumericSearch(domain.harness_space if meta_space == "v2" else space, validate,
                                                 domain.coupling),
                                   (RelayClient(os.environ["RSI_LLM_RELAY"], out / "relay-state.json")
                                    if m.get("relay") else      # addendum 17: Yangquan, key stays on cavin
                                    OpenAICompatClient(m["base_url"], m["model"], m["key_file"])), m["model"],
                                   log_path=out / "meta-llm.jsonl", max_calls=m.get("max_calls", 24),
                                   space_doc=doc,
                                   v2=(dict(rounds=plan["engine"]["rounds"],
                                            inner_steps=plan["engine"].get("inner_steps", 1),
                                            gate_per_task=plan["heldout_per_task"] // 2,
                                            n_tasks=len(domain.tasks)) if meta_space == "v2" else None))
    elif kind == "llm3":                # addendum 29: meta level v3, the LLM behind a harness (workspace, memory, tools)
        from .meta.harness import HarnessMetaProposer, memory_digest
        m = plan["meta"]
        memory = Path(__file__).parent / "meta" / "memory" / m["memory"] if m.get("memory") else None
        if memory is not None and memory_digest(memory) != m["memory_sha256"]:
            raise ValueError("meta_memory_digest_mismatch")       # the memory is frozen before launch
        e = plan["engine"]
        proposer = HarnessMetaProposer(space, validate,
                                       NumericSearch(domain.harness_space if meta_space == "v2" else space, validate,
                                                     domain.coupling),
                                       (RelayClient(os.environ["RSI_LLM_RELAY"], out / "relay-state.json")
                                        if m.get("relay") else
                                        OpenAICompatClient(m["base_url"], m["model"], m["key_file"], timeout=400)),
                                       m["model"], out, memory_dir=memory, max_calls=m.get("max_calls", 60),
                                       max_turns=m.get("max_turns", 6), space_doc=doc,
                                       context=dict(rounds=e["rounds"], inner_steps=e.get("inner_steps", 1),
                                                    gate_per_task=plan["heldout_per_task"] // 2,
                                                    n_tasks=len(domain.tasks),
                                                    children=e.get("candidates_per_round", 1)))
    else:
        raise ValueError(f"unknown_proposer:{kind}")
    cfg = EngineConfig(**plan.get("engine", {}))
    fresh = (domain.fresh_gates(cfg.rounds, len(gate) // len(domain.tasks))
             if cfg.gate_mode == "fresh_paired" else None)
    engine = Engine(domain, backend, initial, program, gate=gate, audit=audit,
                    tests={"libero_official": (domain, test)}, out=out,
                    config=cfg, proposer=proposer,
                    fresh_gates=fresh)
    report = engine.run(resume=args.resume)
    (out / "backend-accounting.json").write_text(json.dumps(dict(
        gpu_seconds=backend.gpu_seconds, admissions=backend.admissions), indent=2, default=str))
    t = report.get("tests", {}).get("libero_official")   # absent when tests are sealed (pilots)
    print(json.dumps(dict(initial=t["initial"], final=t["final"], paired=t["paired"]) if t
                     else dict(status=report.get("status"), retained=report.get("retained"))))


if __name__ == "__main__":
    main()
