"""Run the two-level RSI loop on a VLA policy in LIBERO from a frozen plan.

    python -m rsi.run_libero --plan plan.json --out runs/<new-dir> [--baseline-only --replicates N]
                                                                  [--heldout-eval receipt.json]
                                                                  [--test-eval runs/<ended-run> --replicates N]
                                                                  [--resume]   (continue runs/<dir> in place)

Plan keys: model_name, vla (VLAConfig fields + model_family: openvla | oft, default openvla),
suite, tasks, heldout_per_task,
test_inits_per_task, program (overrides), engine (EngineConfig fields), budget_scale (onebig),
meta {proposer: fixed|numeric}.
"""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .core.gpu import stop_workers_on_sigterm
from .backends.openvla.backend import VLABackend, VLAConfig
from .backends.openvla_oft.backend import OFTBackend
from .core.engine import Engine, EngineConfig
from .core.types import Version
from .domains.libero.domain import LiberoDomain
from .meta.proposers import FixedProgram, NumericSearch

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
    domain = LiberoDomain(plan["suite"], plan["tasks"], plan.get("budget_scale", 1))
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
        node = report["retained"]
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
    proposer = FixedProgram() if kind == "fixed" else NumericSearch(
        domain.edit_space, domain.validate_program, domain.coupling)
    engine = Engine(domain, backend, initial, program, gate=gate, audit=audit,
                    tests={"libero_official": (domain, test)}, out=out,
                    config=EngineConfig(**plan.get("engine", {})), proposer=proposer)
    report = engine.run(resume=args.resume)
    (out / "backend-accounting.json").write_text(json.dumps(dict(
        gpu_seconds=backend.gpu_seconds, admissions=backend.admissions), indent=2, default=str))
    t = report["tests"]["libero_official"]
    print(json.dumps(dict(initial=t["initial"], final=t["final"], paired=t["paired"])))


if __name__ == "__main__":
    main()
