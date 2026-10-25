"""Run the two-level RSI loop on a code world model from a frozen plan.

    python -m rsi.run_code_wm --plan plan.json --out runs/<new-dir> [--baseline-only]

Plan keys: model_name, llm (LLMConfig fields), data {cruxeval, lcb},
heldout {cache, count, seed}, program (overrides of the default improvement
program), engine (EngineConfig fields), meta {proposer: fixed|numeric|self_edit}.
"""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .backends.llm.backend import LLMBackend, LLMConfig
from .core.engine import Engine, EngineConfig
from .core.types import Case, Version
from .domains.code_wm.domain import (CodeWorldModelDomain, InputPredictionSuite, build_heldout,
                                     load_cruxeval, load_lcb_execution, load_mbpp_heldout)
from .meta.proposers import CODE_WM_COUPLING, FixedProgram, NumericSearch, SelfEdit


def merge(base, overrides):
    out = json.loads(json.dumps(base))
    for section, values in (overrides or {}).items():
        out[section].update(values)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--baseline-only", action="store_true")
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text())
    out = Path(args.out)
    if out.exists():
        raise SystemExit("fresh_output_required")
    llm = dict(plan["llm"])
    for key in ("sample_gpus", "train_gpus", "target_modules"):
        if key in llm:
            llm[key] = tuple(llm[key])
    llm.setdefault("workdir", str(out) + ".work")
    backend = LLMBackend(LLMConfig(**llm))
    domain = CodeWorldModelDomain()
    crux_o, crux_i = load_cruxeval(plan["data"]["cruxeval"])
    lcb = load_lcb_execution(plan["data"]["lcb"])
    domain.register_heldout(crux_o + lcb)
    tests = {"cruxeval_o": (domain, crux_o), "cruxeval_i": (InputPredictionSuite(), crux_i),
             "lcb_exec": (domain, lcb)}
    initial = Version(f"base:{plan['model_name']}", llm["base_path"], None)
    if args.baseline_only:
        out.mkdir(parents=True)
        scores = {}
        for name, (suite, cases) in tests.items():
            records = suite.evaluate(backend, initial, cases)
            scores[name] = sum(r.score for r in records) / len(records)
            with (out / f"baseline-{name}.jsonl").open("w") as s:
                for r in records:
                    s.write(json.dumps(asdict(r)) + "\n")
        (out / "baseline.json").write_text(json.dumps(dict(model=plan["model_name"],
                                                           scores=scores), indent=2))
        print(json.dumps(scores))
        return
    program = domain.validate_program(merge(domain.default_program(), plan.get("program")))
    held = plan["heldout"]
    cache = Path(held["cache"])
    if held.get("source") == "mbpp":
        gate, audit = load_mbpp_heldout(held["paths"], domain, held.get("seed", 0))
    elif cache.exists():
        rows = [Case(**json.loads(line)) for line in cache.open()]
        domain.register_heldout(rows)
        gate = [c for c in rows if c.split == "gate"]
        audit = [c for c in rows if c.split == "audit"]
    else:
        gate, audit = build_heldout(domain, backend, initial, program, held["count"], held["seed"])
        cache.parent.mkdir(parents=True, exist_ok=True)
        with cache.open("x") as s:
            for c in gate + audit:
                s.write(json.dumps(asdict(c)) + "\n")
    kind = plan.get("meta", {}).get("proposer", "fixed")
    search = NumericSearch(domain.edit_space, domain.validate_program, CODE_WM_COUPLING)
    proposer = {"fixed": FixedProgram(), "numeric": search,
                "self_edit": SelfEdit(domain.edit_space, domain.validate_program, search)}[kind]
    engine = Engine(domain, backend, initial, program, gate=gate, audit=audit, tests=tests,
                    out=out, config=EngineConfig(**plan.get("engine", {})), proposer=proposer)
    report = engine.run()
    (out / "backend-accounting.json").write_text(json.dumps(dict(
        gpu_seconds=backend.gpu_seconds, admissions=backend.admissions,
        self_edit_log=getattr(proposer, "log", None)), indent=2, default=str))
    print(json.dumps({k: dict(initial=v["initial"], final=v["final"],
                              gain=v["paired"]["mean_gain"], ci=v["paired"]["ci95"])
                      for k, v in report.get("tests", {}).items()} or report["accepted_chain"]))


if __name__ == "__main__":
    main()
