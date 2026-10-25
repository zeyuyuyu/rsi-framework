"""Code world model domain: predict what a program computes; the interpreter is the oracle.

The model writes its own curriculum (short programs + inputs, few-shot from a
pool that grows with its own admitted programs), traces each program K times,
and an attempt is verified only if its answer is a Python literal equal to the
value the sandboxed interpreter computes. The curriculum instruction, solver
settings, curation rule and update operator are all fields of the improvement
program, so the meta level can change how the model teaches itself.

Held-out suites: CRUXEval-O (output prediction), CRUXEval-I (input prediction,
never trained on) and LiveCodeBench execution (different source distribution).
"""

import copy
import json
from pathlib import Path
import random
import re

from ...core.types import Attempt, Case, EvalRecord
from . import prompts as P
from .sandbox import execute_all, static_check

_WS = re.compile(r"\s+")

DEFAULT_PROGRAM = {
    "curriculum": {"proposals": 6000, "max_cases": 3000, "shots": 3, "temperature": 1.0,
                   "instruction": P.PROPOSE_INSTRUCTION, "pool_growth": 500},
    "solver": {"samples": 8, "temperature": 0.8, "top_p": 0.95, "max_tokens": 1024},
    "curation": {"rule": "verified", "budget": 2000, "per_case": 2, "band": [0.0, 1.0]},
    "update": {"operator": "sft", "lr": 1e-4, "steps": 64, "batch": 32},
}

# Declared edit space for the meta level: (min, max) for numbers, choices for categoricals.
EDIT_SPACE = {
    "curriculum.proposals": (100, 12000), "curriculum.max_cases": (50, 4000),
    "curriculum.shots": (1, 6), "curriculum.temperature": (0.6, 1.3),
    "solver.samples": (2, 16), "solver.temperature": (0.4, 1.2),
    "curation.rule": ["verified", "mixed_groups"], "curation.budget": (20, 4000),
    "curation.per_case": (1, 4),
    "update.operator": ["sft", "grpo"], "update.lr": (1e-6, 3e-4), "update.steps": (2, 256),
    "update.batch": (4, 256),
}


def normalize(code):
    return _WS.sub("", code)


def _grams(text, n=10):
    t = normalize(text)
    return {hash(t[i:i + n]) for i in range(max(1, len(t) - n + 1))}


class NearDuplicateIndex:
    """Character n-gram Jaccard against registered programs (inverted index)."""

    def __init__(self, threshold=0.5, n=10):
        self.threshold, self.n, self.sizes, self.index = threshold, n, [], {}

    def add(self, code):
        g = _grams(code, self.n)
        k = len(self.sizes)
        self.sizes.append(len(g))
        for h in g:
            self.index.setdefault(h, []).append(k)

    def max_jaccard(self, code):
        g = _grams(code, self.n)
        shared = {}
        for h in g:
            for k in self.index.get(h, ()):
                shared[k] = shared.get(k, 0) + 1
        return max((s / (len(g) + self.sizes[k] - s) for k, s in shared.items()), default=0.0)

    def hit(self, code):
        return self.max_jaccard(code) >= self.threshold


def get(params, dotted):
    node = params
    for key in dotted.split("."):
        node = node[key]
    return node


def put(params, dotted, value):
    node = params
    keys = dotted.split(".")
    for key in keys[:-1]:
        node = node[key]
    node[keys[-1]] = value


class CodeWorldModelDomain:
    name = "code_world_model"
    higher_is_better = True

    def __init__(self, *, seeds_path=None, workers=48, near_dup_threshold=0.5):
        seeds = json.loads(Path(seeds_path or Path(__file__).with_name("seeds.json")).read_text())
        self.pool = [(s["code"], s["args"]) for s in seeds]
        self.workers = workers
        self.heldout = NearDuplicateIndex(near_dup_threshold)
        self.history = NearDuplicateIndex(0.8)
        self.edit_space = EDIT_SPACE

    # ----------------------------------------------------------- program
    def default_program(self):
        return copy.deepcopy(DEFAULT_PROGRAM)

    def validate_program(self, params):
        out = copy.deepcopy(DEFAULT_PROGRAM)
        for section, values in (params or {}).items():
            if section not in out or not isinstance(values, dict):
                raise ValueError(f"unknown_program_section:{section}")
            for key, value in values.items():
                if key not in out[section]:
                    raise ValueError(f"unknown_program_field:{section}.{key}")
                out[section][key] = value
        for dotted, space in EDIT_SPACE.items():
            value = get(out, dotted)
            if isinstance(space, list):
                if value not in space:
                    raise ValueError(f"program_value_not_allowed:{dotted}")
            else:
                lo, hi = space
                if not isinstance(value, (int, float)) or not lo <= value <= hi:
                    raise ValueError(f"program_value_out_of_range:{dotted}")
        instruction = out["curriculum"]["instruction"]
        if not isinstance(instruction, str) or not 40 <= len(instruction) <= 1500:
            raise ValueError("program_instruction_length")
        if out["curation"]["rule"] == "mixed_groups" and out["update"]["operator"] != "grpo":
            raise ValueError("mixed_groups_requires_grpo")
        if out["update"]["operator"] == "grpo" and out["curation"]["rule"] != "mixed_groups":
            raise ValueError("grpo_requires_mixed_groups")
        return out

    # ----------------------------------------------------------- held-out
    def register_heldout(self, cases):
        for c in cases:
            self.heldout.add(c.inputs["code"])

    def leakage_key(self, case):
        i = case.inputs
        return normalize(i["code"]) + "|" + normalize(i.get("args", i.get("call", "")))

    # ----------------------------------------------------------- prompts & checks
    @staticmethod
    def solve_prompt(case):
        i = case.inputs
        call = i["call"] if "call" in i else f"f({i['args']})"
        return P.fill(P.OUTPUT_COT, code=i["code"], call=call)

    def _check(self, cases, answers):
        jobs = []
        for case, ans in zip(cases, answers):
            i = case.inputs
            if ans is None:
                jobs.append(None)
            elif "call" in i:
                jobs.append(dict(kind="check_call", code=i["code"], call=i["call"], answer=ans,
                                 prelude="from typing import *\n"))
            else:
                jobs.append(dict(kind="check_output", code=i["code"], input=i["args"], answer=ans))
        results = iter(execute_all([j for j in jobs if j is not None], workers=self.workers))
        return [False if j is None else bool(next(results).get("correct")) for j in jobs]

    # ----------------------------------------------------------- RSI hooks
    def propose(self, backend, generator, program, round_index, seed, *, extend_pool=True):
        cur = program["curriculum"]
        rng = random.Random(seed)
        requests = []
        for k in range(int(cur["proposals"])):
            shots = rng.sample(self.pool, min(int(cur["shots"]), len(self.pool)))
            examples = "\n".join(P.example_block(c, a) for c, a in shots)
            requests.append(dict(prompt=P.propose_prompt(cur["instruction"], examples), n=1,
                                 temperature=float(cur["temperature"]), top_p=0.95,
                                 max_tokens=400, stop=P.STOP_PYTHON, seed=seed * 100003 + k))
        texts = [t[0] for t in backend.sample(generator, requests)]
        reasons, parsed, seen = {}, [], set()

        def reject(why):
            reasons[why] = reasons.get(why, 0) + 1

        for text in texts:
            p = P.parse_proposal(text)
            if p is None:
                reject("parse")
                continue
            code, args = p
            if not 3 <= code.count("\n") + 1 <= 20 or len(code) > 900 or len(args) > 150:
                reject("size")
                continue
            why = static_check(code)
            if why:
                reject(why)
                continue
            key = normalize(code) + "|" + normalize(args)
            if key in seen:
                reject("dup_in_round")
                continue
            seen.add(key)
            parsed.append((code, args))
        runs = execute_all([dict(kind="run", code=c, input=a) for c, a in parsed] * 2,
                           workers=self.workers)
        cases = []
        for (code, args), r1, r2 in zip(parsed, runs[:len(parsed)], runs[len(parsed):]):
            if not r1.get("ok"):
                reject("runtime_" + r1.get("error", "?"))
            elif r1 != r2:
                reject("nondeterministic")
            elif not r1.get("round_trip"):
                reject("output_not_literal")
            elif len(r1["output"]) > 120 or r1["output"] == "None":
                reject("output_degenerate")
            elif self.heldout.hit(code):
                reject("near_duplicate_heldout")
            else:
                cases.append((code, args, r1["output"]))
        rng.shuffle(cases)
        cases = cases[:int(cur["max_cases"])]
        self.last_proposal = dict(round=round_index, requested=len(requests),
                                  admitted=len(cases), rejected=reasons)
        if extend_pool:
            self.pool.extend((c, a) for c, a, _ in cases[:int(cur["pool_growth"])])
        out = []
        for k, (code, args, output) in enumerate(cases):
            cid = f"r{round_index}-s{seed}-{k}"
            out.append(Case(cid, cid, "train", dict(code=code, args=args), f"sandbox-exec:{cid}",
                            output))
        return out

    def attempt(self, backend, generator, cases, program, seed):
        sol = program["solver"]
        requests = [dict(prompt=self.solve_prompt(c), n=int(sol["samples"]),
                         temperature=float(sol["temperature"]), top_p=float(sol["top_p"]),
                         max_tokens=int(sol["max_tokens"]), stop=P.STOP_ANSWER,
                         seed=seed * 1000003 + k) for k, c in enumerate(cases)]
        texts = backend.sample(generator, requests)
        flat_cases, answers = [], []
        for c, outs in zip(cases, texts):
            for t in outs:
                flat_cases.append(c)
                answers.append(P.parse_output_answer(t))
        correct = iter(self._check(flat_cases, answers))
        answers = iter(answers)
        result = []
        for c, outs in zip(cases, texts):
            prompt = self.solve_prompt(c)
            tries = []
            for t in outs:
                ans, ok = next(answers), next(correct)
                ok = bool(ok and ans is not None)
                tries.append(Attempt(c.id, float(ok), ok, dict(prompt=prompt, completion=t),
                                     dict(answer=ans, finished="[/ANSWER]" in t)))
            result.append(tries)
        return result

    def evaluate(self, backend, version, cases):
        requests = [dict(prompt=self.solve_prompt(c), n=1, temperature=0.0, top_p=1.0,
                         max_tokens=1024, stop=P.STOP_ANSWER, seed=0) for c in cases]
        texts = [t[0] for t in backend.sample(version, requests)]
        answers = [P.parse_output_answer(t) for t in texts]
        correct = self._check(cases, answers)
        return [EvalRecord(c.id, float(ok), a, dict(text=t[-600:], parsed=a is not None))
                for c, ok, a, t in zip(cases, correct, answers, texts)]

    def signal_metrics(self, cases, attempts):
        rates = [sum(a.verified for a in t) / len(t) for t in attempts]
        novel = 0
        for c in cases[:400]:
            if not self.history.hit(c.inputs["code"]):
                novel += 1
        for c in cases:
            self.history.add(c.inputs["code"])
        lengths = [c.inputs["code"].count("\n") + 1 for c in cases]
        return dict(cases=len(cases), verified_rate=sum(rates) / len(rates),
                    mixed_fraction=sum(0 < r < 1 for r in rates) / len(rates),
                    unsolved_fraction=sum(r == 0 for r in rates) / len(rates),
                    novelty_vs_history=novel / max(1, min(400, len(cases))),
                    mean_lines=sum(lengths) / len(lengths),
                    finished_rate=sum(a.details["finished"] for t in attempts for a in t)
                    / sum(len(t) for t in attempts),
                    proposal=getattr(self, "last_proposal", {}))


class InputPredictionSuite:
    """CRUXEval-I transfer suite (evaluation only)."""
    higher_is_better = True

    def __init__(self, workers=48):
        self.workers = workers

    def leakage_key(self, case):
        return normalize(case.inputs["code"]) + "|" + normalize(case.inputs["args"])

    def evaluate(self, backend, version, cases):
        requests = [dict(prompt=P.fill(P.INPUT_COT, code=c.inputs["code"], output=c.label),
                         n=1, temperature=0.0, top_p=1.0, max_tokens=1024, stop=P.STOP_ANSWER,
                         seed=0) for c in cases]
        texts = [t[0] for t in backend.sample(version, requests)]
        answers = [P.parse_input_answer(t) for t in texts]
        jobs = [dict(kind="check_input", code=c.inputs["code"], output=c.label, answer=a)
                for c, a in zip(cases, answers) if a is not None]
        results = iter(execute_all(jobs, workers=self.workers))
        return [EvalRecord(c.id, float(a is not None and bool(next(results).get("correct"))), a,
                           dict(text=t[-600:])) for c, a, t in zip(cases, answers, texts)]


def load_cruxeval(path):
    rows = [json.loads(line) for line in open(path) if line.strip()]
    out_cases = [Case(f"cruxO-{r['id']}", f"cruxeval-{r['id']}", "test",
                      dict(code=r["code"], args=r["input"]), f"cruxeval@test:{r['id']}", r["output"])
                 for r in rows]
    in_cases = [Case(f"cruxI-{r['id']}", f"cruxeval-{r['id']}", "test",
                     dict(code=r["code"], args=r["input"]), f"cruxeval@test:{r['id']}", r["output"])
                for r in rows]
    return out_cases, in_cases


def load_lcb_execution(path):
    import pandas as pd
    d = pd.read_parquet(path)
    return [Case(f"lcbx-{r['id']}", f"lcbx-{r['question_id']}", "test",
                 dict(code=r["code"], call=r["input"]),
                 f"livecodebench/execution-v2@test:{r['id']}", r["output"])
            for _, r in d.iterrows()]


def build_heldout(domain, backend, initial, program, count, seed):
    """Gate + audit programs proposed by the INITIAL model before any training.

    Never added to the few-shot pool; registered as held-out so later
    training proposals that near-duplicate them are rejected.
    """
    params = copy.deepcopy(program)
    params["curriculum"]["proposals"] = max(count * 3, 600)
    params["curriculum"]["max_cases"] = count
    cases = domain.propose(backend, initial, params, 0, seed, extend_pool=False)
    out = []
    for k, c in enumerate(cases):
        split = "gate" if k % 2 == 0 else "audit"
        out.append(Case(f"{split}-{c.id}", f"{split}-{c.group}", split, c.inputs,
                        f"sandbox-exec:{split}-{c.id}", c.label))
    domain.register_heldout(out)
    return [c for c in out if c.split == "gate"], [c for c in out if c.split == "audit"]
