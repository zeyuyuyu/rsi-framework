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
from rsi.core.gpu import occupied
from rsi.domains.libero.domain import LiberoDomain
import rsi.backends.openvla.backend as vla_backend
import rsi.backends.llm.backend as llm_backend
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

    def test_candidates_of_a_round_share_its_cases(self):
        # The meta level edits only the solver: the second candidate re-proposes the round's placements.
        class SolverEdit:
            def propose(self, program, archive, backend, version, n, rng):
                return [Program.make(dict(program.params, solver={"t": rng.random()}), program.id, "search", "")]

        e, _ = self.engine("share", proposer=SolverEdit(), rounds=2, candidates_per_round=2)
        e.run()
        r1 = json.loads((self.tmp / "share" / "round-01.json").read_text())
        self.assertEqual(len(r1["candidates"]), 2)
        self.assertTrue(all(c["gate"] is not None for c in r1["candidates"]))
        self.assertEqual({c["signal"]["rejected"]["duplicate"] for c in r1["candidates"]}, {0})
        r2 = json.loads((self.tmp / "share" / "round-02.json").read_text())
        self.assertTrue(all(c["gate"] is not None for c in r2["candidates"]))

    def test_inner_steps_train_on_policy_on_fresh_cases(self):
        class SeededToy(ToyDomain):
            def propose(self, backend, generator, program, round_index, seed):
                self.calls.append(("propose", generator.id))
                return [Case(f"r{round_index}-s{seed}-{i}", f"g{i}", "train", {"d": i / 10}, "toy")
                        for i in range(10)]

        def run(name, **cfg):
            domain, backend = SeededToy(), ToyBackend()
            e = Engine(domain, backend, Version("init", "/b"), domain.default_program(),
                       gate=heldout("gate", 20), audit=heldout("audit", 20),
                       tests={"t": (domain, heldout("test", 40))}, out=self.tmp / name,
                       config=EngineConfig(**cfg), proposer=FixedProgram())
            return e.run(), domain, backend

        rep, domain, backend = run("inner", rounds=2, inner_steps=3)
        r1 = json.loads((self.tmp / "inner" / "round-01.json").read_text())
        inner = r1["candidates"][0]["signal"]["inner"]
        self.assertEqual([s["trained"] for s in inner], [True, True, True])
        gens = [g for kind, g in domain.calls if kind == "propose"][:3]
        self.assertEqual(gens[0], "init")
        self.assertEqual(gens[1:], [inner[0]["version"], inner[1]["version"]])   # samples with what it just trained
        self.assertEqual({s["signal"]["rejected"]["duplicate"] for s in inner}, {0})  # fresh cases every step
        self.assertTrue((self.tmp / "inner" / "ckpt-r01c0" / "w.bin").exists())
        # one gate per round, after three updates: the chain gains more per round than inner_steps=1
        one, _, _ = run("one", rounds=2)
        self.assertGreater(rep["tests"]["t"]["final"], one["tests"]["t"]["final"])
        _, domain_nr, _ = run("inner_nonrec", rounds=1, inner_steps=3, recursive=False)
        self.assertTrue(all(g == "init" for kind, g in domain_nr.calls if kind == "propose"))

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

    def test_resume_after_a_kill_matches_the_uninterrupted_run(self):
        class Killed(ToyBackend):
            calls, kill_at = 0, None

            def train(self, parent, items, output, update, seed):
                self.calls += 1
                if self.calls == self.kill_at:
                    output.mkdir()                       # a half-written checkpoint
                    raise RuntimeError("job wall time")
                return super().train(parent, items, output, update, seed)

        def make(name, backend):
            domain = ToyDomain()
            return Engine(domain, backend, Version("init", "/b"), domain.default_program(),
                          gate=heldout("gate", 20), audit=heldout("audit", 20),
                          tests={"t": (domain, heldout("test", 40))}, out=self.tmp / name,
                          config=EngineConfig(rounds=3), proposer=FixedProgram())

        whole = make("whole", ToyBackend()).run()
        backend = Killed()
        backend.kill_at = 3
        with self.assertRaises(RuntimeError):
            make("killed", backend).run()
        self.assertTrue((self.tmp / "killed" / "ckpt-r03c0").exists())
        backend.kill_at = None
        resumed = make("killed", backend).run(resume=True)
        self.assertEqual(resumed["retained"], whole["retained"])
        self.assertEqual([(n["node"], n["gate"]) for n in resumed["accepted_chain"]],
                         [(n["node"], n["gate"]) for n in whole["accepted_chain"]])
        self.assertEqual(resumed["tests"]["t"]["final"], whole["tests"]["t"]["final"])
        aside = sorted(p.name for p in (self.tmp / "killed" / "resume-03").iterdir())
        self.assertIn("ckpt-r03c0", aside)
        self.assertIn("failure.json", aside)
        record = json.loads((self.tmp / "killed" / "resume.json").read_text())
        self.assertEqual(record["completed_rounds"], 2)
        with open(self.tmp / "killed" / "accepted.jsonl") as stream:
            self.assertEqual([json.loads(l)["round"] for l in stream], [1, 2, 3])

    def test_resume_refuses_a_different_plan(self):
        e, _ = self.engine("plan", rounds=1)
        e.run()
        (self.tmp / "plan" / "report.json").unlink()
        e2, _ = self.engine("plan", rounds=2)
        with self.assertRaises(ValueError):
            e2.run(resume=True)

    def test_rejected_candidates_are_released_accepted_ones_kept(self):
        class Releasing(ToyBackend):
            def __init__(self):
                super().__init__()
                self.released = []

            def release(self, version):
                self.released.append(version.id)

        domain, backend = ToyDomain(), Releasing()
        e = Engine(domain, backend, Version("init", "/b"), domain.default_program(),
                   gate=heldout("gate", 20), audit=heldout("audit", 20),
                   tests={"t": (domain, heldout("test", 40))}, out=self.tmp / "rel",
                   config=EngineConfig(rounds=2, min_gate_gain=10.0), proposer=FixedProgram())
        rep = e.run()
        self.assertEqual(rep["retained"], "n0")
        self.assertEqual(len(backend.released), 2)                    # both rounds' candidates rejected
        e2, _ = self.engine("kept", rounds=2)
        e2.backend.release = lambda v: self.fail("an accepted candidate must not be released")
        e2.run()

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


class GpuAdmissionTests(unittest.TestCase):
    def test_idle_foreign_context_does_not_block_but_busy_work_does(self):
        self.assertFalse(occupied((845, 0)))       # nothing there
        self.assertFalse(occupied((7425, 0)))      # parked CI context, idle
        self.assertTrue(occupied((8753, 94)))      # another user's running job
        self.assertTrue(occupied((12000, 0)))      # too large to share even if idle


class VLAPhaseRetryTests(unittest.TestCase):
    def _backend(self, tmp):
        cfg = vla_backend.VLAConfig(checkpoint="ck", python="py", openvla_root="root", workdir=tmp)
        backend = vla_backend.VLABackend(cfg)
        call = backend._call_dir("rollout")
        return backend, call

    def _fake_phase(self, call, failures):
        attempts = []

        def phase(call_, tag, *args):
            n = len(attempts)
            attempts.append(n)
            eps = call / "episodes"
            eps.mkdir(exist_ok=True)
            (eps / f"results-{100 + n}.jsonl").write_text(json.dumps({"id": "e1", "attempt": n}) + "\n")
            (eps / "e1.npz").write_text(f"attempt {n}")
            if n < len(failures):
                log = call / f"log-{tag}0.txt"
                log.write_text(failures[n])
                raise RuntimeError(f"parallel_worker_failed:['{log}']")
        return phase, attempts

    def test_oom_phase_is_rerun_and_failed_attempt_set_aside(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend, call = self._backend(tmp)
            phase, attempts = self._fake_phase(call, ["torch.cuda.OutOfMemoryError: CUDA out of memory. Tried"])
            backend._phase = phase
            original, vla_backend.admit = vla_backend.admit, lambda gpus, gap, **kw: {"ok": True, "gpus": list(gpus)}
            try:
                backend._phase_retrying(call, "g")
            finally:
                vla_backend.admit = original
            self.assertEqual(attempts, [0, 1])
            kept = sorted(p.name for p in (call / "episodes").iterdir())
            self.assertEqual(kept, ["e1.npz", "results-101.jsonl"])
            self.assertEqual((call / "episodes" / "e1.npz").read_text(), "attempt 1")
            self.assertEqual(sorted(p.name for p in (call / "discarded-g0").iterdir()),
                             ["e1.npz", "log-g0.txt", "results-100.jsonl"])
            self.assertEqual(backend.admissions[-1]["retry_of"], "g0")

    def test_non_oom_failure_is_not_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend, call = self._backend(tmp)
            phase, attempts = self._fake_phase(call, ["ValueError: bad spec"])
            backend._phase = phase
            with self.assertRaises(RuntimeError):
                backend._phase_retrying(call, "s")
            self.assertEqual(attempts, [0])

    def test_gives_up_after_configured_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            backend, call = self._backend(tmp)
            phase, attempts = self._fake_phase(call, ["CUDA out of memory"] * 3)
            backend._phase = phase
            original, vla_backend.admit = vla_backend.admit, lambda gpus, gap, **kw: {"gpus": list(gpus)}
            try:
                with self.assertRaises(RuntimeError):
                    backend._phase_retrying(call, "s")
            finally:
                vla_backend.admit = original
            self.assertEqual(attempts, [0, 1, 2])


class OFTTests(unittest.TestCase):
    """Pure parts of the OpenVLA-OFT backend (no model, no simulator)."""

    def test_decode_chunk_bins_unnormalises_q99_and_keeps_action_order(self):
        import numpy as np
        from rsi.backends.openvla_oft.rollout_worker import decode_chunk
        bins = np.linspace(-1, 1, 256)
        centres = (bins[:-1] + bins[1:]) / 2
        q01, q99 = np.array([-1.0, 0, 0, 0, 0, -2, 0]), np.array([1.0, 2, 2, 2, 2, 2, 1])
        stats = {"q01": q01.tolist(), "q99": q99.tolist(), "mask": [True] * 6 + [False]}
        tokens = np.full((2, 56), 31999)            # lowest bin everywhere
        tokens[1, 7:14] = 31744                     # highest bin: second action of the second chunk
        tokens[1, 14] = 31872                       # a middle bin
        tokens[1, 15] = 32005                       # beyond the action ids: clipped to the lowest bin
        a = decode_chunk(tokens, centres, 32000, stats)
        self.assertEqual(a.shape, (2, 8, 7))
        unnorm = lambda n: 0.5 * (n + 1) * (q99 - q01 + 1e-8) + q01
        low = np.where(stats["mask"], unnorm(centres[0]), centres[0])
        np.testing.assert_allclose(a[0], np.tile(low, (8, 1)), rtol=0, atol=1e-12)
        np.testing.assert_allclose(a[1, 1, :6], unnorm(centres[254])[:6], rtol=0, atol=1e-12)
        self.assertEqual(a[1, 1, 6], centres[254])  # gripper stays normalised (mask False)
        self.assertAlmostEqual(a[1, 2, 0], unnorm(centres[127])[0], places=12)
        self.assertAlmostEqual(a[1, 2, 1], unnorm(centres[0])[1], places=12)
        np.testing.assert_allclose(a[1, 0], low, rtol=0, atol=1e-12)

    def test_chunks_run_until_success_or_the_step_budget(self):
        from rsi.backends.openvla_oft.rollout_worker import MAX_STEPS, run_chunk

        def env(done_at):
            calls = []

            def step(action):
                calls.append(action)
                return len(calls), 0.0, len(calls) == done_at, {}
            return step, calls
        step, calls = env(done_at=3)
        self.assertEqual(run_chunk(step, list(range(8)), 0, MAX_STEPS), (3, 3, True))
        self.assertEqual(calls, [0, 1, 2])
        step, _ = env(done_at=None)
        self.assertEqual(run_chunk(step, list(range(8)), 0, MAX_STEPS), (8, 8, False))
        step, calls = env(done_at=None)
        self.assertEqual(run_chunk(step, list(range(8)), MAX_STEPS - 3, MAX_STEPS), (3, 3, False))
        step, _ = env(done_at=None)
        steps, chunks = 0, 0
        while steps < MAX_STEPS:
            _, k, ok = run_chunk(step, list(range(8)), steps, MAX_STEPS)
            steps, chunks = steps + k, chunks + 1
        self.assertEqual((steps, chunks, MAX_STEPS), (512, 64, 512))

    def test_training_counts_only_tokens_of_executed_actions(self):
        from rsi.backends.openvla_oft.train_worker import token_mask
        m = token_mask([8, 3, 1])
        self.assertEqual(m.shape, (3, 56))
        self.assertTrue(m[0].all())
        self.assertEqual(m[1].tolist(), [True] * 21 + [False] * 35)
        self.assertEqual(int(m[2].sum()), 7)

    def test_plan_model_family_selects_backend_and_its_workers(self):
        from rsi.backends.openvla_oft.backend import OFTBackend
        from rsi.run_libero import make_backend
        with tempfile.TemporaryDirectory() as tmp:
            base = dict(checkpoint="ck", python="py", openvla_root="root", workdir=tmp)
            self.assertIs(type(make_backend(base)), vla_backend.VLABackend)
            oft = make_backend(dict(base, model_family="oft"))
            self.assertIs(type(oft), OFTBackend)
            with self.assertRaises(SystemExit):
                make_backend(dict(base, model_family="pi0"))
            jobs = []
            original = vla_backend.supervised_parallel
            vla_backend.supervised_parallel = lambda js, timeout: jobs.extend(js)
            try:
                call = oft._call_dir("rollout")
                oft._phase(call, "g", None, "libero_10",
                           [dict(id="e", task_id=0, mode="greedy", temperature=0.0)], None, 1, 1)
            finally:
                vla_backend.supervised_parallel = original
            self.assertEqual(Path(jobs[0][0][1]).parent.name, "openvla_oft")
            self.assertEqual(json.loads((call / "spec-g0.json").read_text())["openvla_root"], "root")


class LLMSampleRetryTests(unittest.TestCase):
    def test_oom_sampling_call_is_rerun_with_fresh_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "base").mkdir()
            backend = llm_backend.LLMBackend(llm_backend.LLMConfig(
                base_path=str(tmp / "base"), python="py", workdir=str(tmp / "work")))
            attempts = []

            def fake_parallel(jobs, timeout):
                argv, gpus, log, env = jobs[0]
                out = Path(argv[argv.index("--out") + 1])
                attempts.append(len(attempts))
                if len(attempts) == 1:
                    out.write_text(json.dumps(dict(index=0, texts=["stale"])) + "\n")
                    log.write_text("torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 1.74 GiB")
                    raise RuntimeError(f"parallel_worker_failed:['{log}']")
                out.write_text("".join(json.dumps(dict(index=i, texts=[f"ok{i}"])) + "\n" for i in range(2)))

            originals = llm_backend.supervised_parallel, llm_backend.admit
            llm_backend.supervised_parallel = fake_parallel
            llm_backend.admit = lambda gpus, gap: {}
            try:
                texts = backend.sample(Version("base", str(tmp / "base")), [dict(prompt="a", n=1), dict(prompt="b", n=1)])
            finally:
                llm_backend.supervised_parallel, llm_backend.admit = originals
            self.assertEqual(texts, [["ok0"], ["ok1"]])
            self.assertEqual(attempts, [0, 1])
            call = next((tmp / "work").iterdir())
            self.assertEqual(sorted(p.name for p in (call / "discarded-0").iterdir()), ["log-0.txt", "out-0.jsonl"])


class WorkerCleanupTests(unittest.TestCase):
    def test_sigterm_to_the_runner_stops_its_workers(self):
        import os, signal, subprocess, sys, time
        with tempfile.TemporaryDirectory() as tmp:
            pidfile = Path(tmp) / "child.pid"
            runner = (
                "import sys; sys.path.insert(0, %r)\n"
                "from rsi.core.gpu import stop_workers_on_sigterm, supervised\n"
                "stop_workers_on_sigterm()\n"
                "supervised(['bash', '-c', 'echo $$ > %s; exec sleep 60'], gpus=[], timeout=120, log_path=%r)\n"
            ) % (str(Path(__file__).resolve().parent), pidfile, str(Path(tmp) / "log.txt"))
            proc = subprocess.Popen([sys.executable, "-c", runner])
            for _ in range(100):
                if pidfile.exists() and pidfile.read_text().strip():
                    break
                time.sleep(0.05)
            child = int(pidfile.read_text())
            proc.send_signal(signal.SIGTERM)
            self.assertEqual(proc.wait(timeout=10), 128 + signal.SIGTERM)
            for _ in range(100):
                try:
                    os.kill(child, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.05)
            else:
                self.fail("worker survived the runner's SIGTERM")


class AdmitSubsetTests(unittest.TestCase):
    def _run(self, readings, **kw):
        import rsi.core.gpu as g
        it = iter(readings)
        saved = g.gpu_status, g.time.sleep
        g.gpu_status, g.time.sleep = (lambda: next(it)), (lambda s: None)
        try:
            return g.admit([0, 1], gap=0, poll=60, **kw)
        finally:
            g.gpu_status, g.time.sleep = saved

    def test_busy_second_gpu_falls_back_to_the_free_one_after_full_wait(self):
        busy = {0: (100, 0), 1: (14000, 90)}
        adm = self._run([busy] * 40, min_gpus=1, full_wait=300, wait_seconds=3600)
        self.assertEqual(adm["gpus"], [0])
        self.assertGreaterEqual(adm["waited_seconds"], 300)

    def test_without_min_gpus_every_gpu_is_still_required(self):
        busy = {0: (100, 0), 1: (14000, 90)}
        with self.assertRaises(RuntimeError):
            self._run([busy] * 400, wait_seconds=-1)

    def test_all_free_admits_all(self):
        free = {0: (100, 0), 1: (100, 0)}
        self.assertEqual(self._run([free, free], min_gpus=1, full_wait=300)["gpus"], [0, 1])


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

    def test_libero_budget_scale_only_widens_counts(self):
        big = {"curriculum": {"cases": 960}, "curation": {"budget": 2400}, "update": {"steps": 600}}
        with self.assertRaises(ValueError):
            LiberoDomain("libero_10", range(10)).validate_program(big)
        d = LiberoDomain("libero_10", range(10), budget_scale=6)
        self.assertEqual(d.validate_program(big)["curriculum"]["cases"], 960)
        with self.assertRaises(ValueError):                              # non-count fields keep their bounds
            d.validate_program({"update": {"lr": 1e-3}})
        self.assertEqual(d.edit_space["curriculum.cases"], (40, 400))   # the meta level's space is unchanged

    def test_inner_seeds_stay_in_range_unique_and_keep_seed0(self):
        from rsi.core.engine import inner_seed
        d = LiberoDomain("libero_10", range(10))
        prog = d.validate_program({"curriculum": {"cases": 64}})
        seen = {}
        for run_seed in range(4):
            for r in range(1, 10):
                for it in range(3):
                    s = inner_seed(run_seed, r, it)
                    self.assertNotIn(s, seen)                                     # no shared placements
                    seen[s] = (run_seed, r, it)
                    if run_seed == 0 and it:
                        self.assertEqual(s, (0 * 1000 + r) * 100 + it)          # pilot-5 seeds unchanged
                    for case in d.propose(None, None, prog, r, s):                # raises if past 2**32
                        self.assertLess(case.inputs["init"]["seed"], 2 ** 32)
        with self.assertRaises(ValueError):
            d.propose(None, None, prog, 1, 1001 * 100 + 1)                       # the old seed-1 value
        with self.assertRaises(ValueError):
            inner_seed(1, 10, 1)

    def test_matched_ratio_reaches_only_the_oft_train_spec(self):
        from unittest import mock
        from rsi.backends.openvla import backend as vb
        from rsi.backends.openvla_oft.backend import OFTBackend
        from rsi.core.types import Version
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):                          # the OpenVLA worker has no such mode
                vb.VLABackend(vb.VLAConfig("ck", "py", "root", tmp, ratio_mode="matched"))
            specs = {}
            for mode in ("legacy", "matched"):
                be = OFTBackend(vb.VLAConfig("ck", "py", "root", f"{tmp}/{mode}", ratio_mode=mode))
                with mock.patch.object(vb, "admit"), mock.patch.object(vb, "supervised", side_effect=RuntimeError):
                    with self.assertRaises(RuntimeError):
                        be.train(Version("v0", "ck", None), [{"episode": "e"}], f"{tmp}/out", {"lr": 1e-4}, 0)
                specs[mode] = json.loads(next(Path(f"{tmp}/{mode}").glob("*-train-*/train_spec.json")).read_text())
            self.assertEqual(specs["legacy"]["update"], {"lr": 1e-4})    # legacy specs are unchanged
            self.assertEqual(specs["matched"]["update"], {"lr": 1e-4, "ratio": "matched"})


if __name__ == "__main__":
    unittest.main()
