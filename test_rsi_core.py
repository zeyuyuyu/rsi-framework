"""Offline checks of the two-level RSI engine (no models, no GPU)."""

import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest

from rsi.core.archive import Archive, Node, program_diff
from rsi.core.curation import curate, shuffle_feedback
from rsi.core.engine import Engine, EngineConfig
from rsi.core.types import Attempt, Case, EvalRecord, Program, Receipt, Version
from rsi.domains.code_wm.domain import CodeWorldModelDomain
from rsi.meta.proposers import CODE_WM_COUPLING, FixedProgram, NumericSearch


class ToyDomain:
    """Skill s solves a case iff its difficulty < s. Training raises skill by the
    number of verified items (capped) when feedback is real; the program knob
    ``boost`` scales the gain, so a better program is measurably better."""
    name = "toy"
    higher_is_better = True

    def __init__(self):
        self.calls = []

    def default_program(self):
        return {"curation": {"rule": "verified", "budget": 50, "per_case": 1, "band": [0.0, 1.0]},
                "update": {"operator": "sft", "boost": 1}, "curriculum": {}, "solver": {}}

    def validate_program(self, params):
        if params["update"]["boost"] not in (1, 2, 3):
            raise ValueError("boost")
        return params

    def leakage_key(self, case):
        return case.id

    def propose(self, backend, generator, program, round_index, seed):
        self.calls.append(("propose", generator.id))
        return [Case(f"r{round_index}-{i}", f"g{i}", "train", {"d": i / 10}, "toy") for i in range(10)]

    def attempt(self, backend, generator, cases, program, seed):
        s = backend.skill[generator.id]
        return [[Attempt(c.id, float(c.inputs["d"] < s), c.inputs["d"] < s, {"c": c.id})
                 for _ in range(4)] for c in cases]

    def evaluate(self, backend, version, cases):
        s = backend.skill[version.id]
        return [EvalRecord(c.id, float(c.inputs["d"] < s)) for c in cases]

    def signal_metrics(self, cases, attempts):
        return {"verified_rate": sum(a.verified for t in attempts for a in t) / sum(len(t) for t in attempts)}


class ToyBackend:
    def __init__(self):
        self.skill = {"init": 0.25}

    def train(self, parent, items, output, update, seed):
        output.mkdir()
        (output / "w.bin").write_text("x")
        gain = 0.1 * update["boost"] * (1 if items and all("c" in i for i in items) else 0)
        before = hashlib.sha256(parent.id.encode()).hexdigest()
        after = hashlib.sha256((parent.id + output.name).encode()).hexdigest()
        vid = "v" + after[:10]
        self.skill[vid] = min(1.0, self.skill[parent.id] + gain)
        return Receipt(Version(vid, str(output), parent.id), "sft", 3, len(items), 5, before, after)


def heldout(split, n):
    return [Case(f"{split}{i}", f"{split}{i}", split, {"d": (i + 0.5) / n}, "toy") for i in range(n)]


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def engine(self, name, proposer=None, **cfg):
        domain, backend = ToyDomain(), ToyBackend()
        e = Engine(domain, backend, Version("init", "/b"), domain.default_program(),
                   gate=heldout("gate", 20), audit=heldout("audit", 20),
                   tests={"t": (domain, heldout("test", 40))}, out=self.tmp / name,
                   config=EngineConfig(**cfg), proposer=proposer or FixedProgram())
        return e, domain

    def test_recursive_chain_improves_and_is_reported(self):
        e, _ = self.engine("rec", rounds=3)
        rep = e.run()
        self.assertEqual(len(rep["accepted_chain"]), 4)
        self.assertGreater(rep["tests"]["t"]["final"], rep["tests"]["t"]["initial"])
        for f in ("plan.json", "archive.jsonl", "accepted.jsonl", "round-01.json",
                  "retained.json", "report.json"):
            self.assertTrue((self.tmp / "rec" / f).exists(), f)

    def test_non_recursive_control_uses_initial_generator(self):
        e, domain = self.engine("nonrec", rounds=3, recursive=False)
        e.run()
        self.assertTrue(all(g == "init" for kind, g in domain.calls if kind == "propose"))

    def test_shuffled_feedback_keeps_counts(self):
        rng = random.Random(0)
        tries = [[Attempt("a", 1.0, True, {}), Attempt("a", 0.0, False, {})]]
        out = shuffle_feedback(tries, rng)
        self.assertEqual(sum(a.verified for a in out[0]), 1)

    def test_meta_search_selects_better_program(self):
        domain = ToyDomain()
        space = {"update.boost": [1, 2, 3]}
        e, _ = self.engine("meta", proposer=NumericSearch(space, domain.validate_program),
                           rounds=2, candidates_per_round=3)
        rep = e.run()
        with open(self.tmp / "meta" / "accepted.jsonl") as stream:
            boosts = [json.loads(l)["program"] for l in stream]
        self.assertTrue(boosts)
        chain_authors = [n["author"] for n in rep["accepted_chain"][1:]]
        self.assertIn("search", chain_authors)

    def test_test_suites_use_their_own_evaluator(self):
        class Constant:
            higher_is_better = True

            def leakage_key(self, case):
                return "const|" + case.id

            def evaluate(self, backend, version, cases):
                return [EvalRecord(c.id, 0.5) for c in cases]

        domain, backend = ToyDomain(), ToyBackend()
        e = Engine(domain, backend, Version("init", "/b"), domain.default_program(),
                   gate=heldout("gate", 20), audit=heldout("audit", 20),
                   tests={"t": (domain, heldout("test", 40)), "c": (Constant(), heldout("test", 4))},
                   out=self.tmp / "suites", config=EngineConfig(rounds=2), proposer=FixedProgram())
        rep = e.run()
        self.assertEqual(rep["tests"]["c"]["initial"], 0.5)
        self.assertEqual(rep["tests"]["c"]["final"], 0.5)
        self.assertNotEqual(rep["tests"]["t"]["final"], 0.5)

    def test_regression_is_rejected(self):
        e, _ = self.engine("rej", rounds=2, min_gate_gain=10.0)
        rep = e.run()
        self.assertEqual(rep["retained"], "n0")
        self.assertEqual(rep["tests"]["t"]["initial"], rep["tests"]["t"]["final"])


class CurationTests(unittest.TestCase):
    def setUp(self):
        self.cases = [Case(f"c{i}", f"c{i}", "train", {}, "o") for i in range(4)]
        self.attempts = [[Attempt(c.id, float(k < i), k < i, {"k": k}) for k in range(4)]
                         for i, c in enumerate(self.cases)]

    def test_verified_hardest_first_with_cap(self):
        items, ids, stats = curate(self.cases, self.attempts,
                                   {"rule": "verified", "budget": 10, "per_case": 2}, random.Random(0))
        self.assertEqual(ids, ["c1", "c2", "c2", "c3", "c3"])
        self.assertEqual(stats["mixed_cases"], 3)

    def test_mixed_groups_advantages_sum_to_zero(self):
        items, ids, stats = curate(self.cases, self.attempts,
                                   {"rule": "mixed_groups", "budget": 10}, random.Random(0))
        self.assertEqual(len(items), 12)          # cases 1..3, 4 attempts each
        by = {}
        for i, cid in zip(items, ids):
            by.setdefault(cid, []).append(i["advantage"])
        self.assertTrue(all(abs(sum(v)) < 1e-9 for v in by.values()))


class SandboxTrustTests(unittest.TestCase):
    def test_benchmark_inputs_may_be_expressions_but_model_inputs_may_not(self):
        from rsi.domains.code_wm.sandbox import execute
        code = "def f(s):\n    return len(s)"
        job = dict(kind="check_output", code=code, input="''.join(['A'] * 20)", answer="20")
        self.assertTrue(execute(dict(job, trusted=True))["correct"])
        self.assertFalse(execute(job).get("correct", False))
        self.assertTrue(execute(dict(kind="check_output", code="def f():\n    return 5",
                                     input="", answer="5"))["correct"])
        # the model's answer is never evaluated as code, trusted input or not
        self.assertFalse(execute(dict(job, trusted=True, answer="f('a' * 20)"))["correct"])


class PathologicalTextTests(unittest.TestCase):
    def test_deeply_nested_model_text_is_rejected_not_crashing(self):
        from rsi.domains.code_wm import prompts as P
        from rsi.domains.code_wm.sandbox import static_check
        deep = "[" * 20000 + "]" * 20000
        self.assertIsNone(P.parse_output_answer("[ANSWER]\nassert f(1) == " + deep + "\n[/ANSWER]"))
        self.assertIsNone(P.parse_input_answer("[ANSWER]\nassert f(" + deep + ") == 1\n[/ANSWER]"))
        self.assertIsNone(P.parse_proposal("def f(x):\n    return x\nassert f(" + deep + ") == ??"))
        self.assertIsNotNone(static_check("def f(x):\n    return " + deep))
        self.assertEqual(P.parse_output_answer("[ANSWER]\nassert f(1) == [1, [2]]\n[/ANSWER]"), "[1, [2]]")


class ProgramTests(unittest.TestCase):
    def test_code_wm_program_validation_and_search(self):
        d = CodeWorldModelDomain()
        p = d.validate_program(d.default_program())
        with self.assertRaises(ValueError):
            d.validate_program({"update": {"lr": 10.0}})
        with self.assertRaises(ValueError):
            d.validate_program({"update": {"operator": "grpo"}})       # needs mixed_groups
        ns = NumericSearch(d.edit_space, d.validate_program, CODE_WM_COUPLING)
        archive = Archive(Path(tempfile.mkdtemp()) / "a.jsonl")
        archive.add(Node("n0", 0, Version("i", "/b"), Program.make(p), None, gate=0.4, accepted=True))
        out = ns.propose(Program.make(p), archive, None, None, 4, random.Random(1))
        self.assertEqual(len(out), 4)
        self.assertTrue(all(o.params != p for o in out))
        self.assertEqual(program_diff({"a": {"b": 1}}, {"a": {"b": 2}}), {"a.b": 2})


if __name__ == "__main__":
    unittest.main()
