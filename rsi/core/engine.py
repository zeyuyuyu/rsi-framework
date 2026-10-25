"""The two-level recursive self-improvement loop.

Object level (every round, from the selected parent node):
    generator := parent model (recursive) | initial model (non-recursive control)
    cases     := domain.propose(generator, program)   - the model writes its own tasks
    attempts  := domain.attempt(generator, cases)     - and its own solutions
    verify    := the domain's external oracle scores each attempt
    items     := curate(program.curation)             - verified experience
    child     := backend.train(parent, items, program.update)
Meta level (the same round):
    candidate programs := incumbent + meta_proposer(parent program, archive)
    each candidate runs the object level; the gate set picks the best;
    the child (and the program that produced it) is accepted only if the gate
    score does not drop. Accepted programs are inherited by later rounds.

Held-out data is split three ways: ``gate`` decides acceptance and program
selection, ``audit`` is scored for every accepted node but never decides
anything (it exposes overfitting to the gate), and ``test`` suites are read
only after the last round. The controls that make a recursion claim
falsifiable are configuration, not separate code:
    recursive=False        frozen initial model generates every round's data
    feedback="shuffled"    oracle labels permuted within each case
    meta=fixed proposer    the seed program is never changed
"""

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import random
import time

from .archive import Archive, Node
from .curation import curate, shuffle_feedback
from .types import Program, Version, canonical, digest


@dataclass(frozen=True)
class EngineConfig:
    rounds: int = 3
    seed: int = 0
    recursive: bool = True
    feedback: str = "true"            # true | shuffled
    candidates_per_round: int = 1     # programs tried per round (incumbent included)
    min_gate_gain: float = 0.0
    wall_seconds: int = 14 * 24 * 3600
    test_all_accepted: bool = True
    # Pilots (development decisions on the gate set) must not read test suites at all.
    seal_tests: bool = False


def _write(path: Path, data):
    with path.open("x") as stream:
        stream.write(json.dumps(data, indent=2, sort_keys=True, default=str) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _jsonl(path: Path, rows):
    with path.open("x") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False, default=str) + "\n")


def _mean(records):
    return sum(r.score for r in records) / len(records)


class Engine:
    def __init__(self, domain, backend, initial: Version, seed_program: dict, *,
                 gate, audit, tests: dict, out: Path, config: EngineConfig, proposer):
        self.domain, self.backend, self.initial = domain, backend, initial
        self.seed_program = Program.make(domain.validate_program(seed_program))
        self.gate, self.audit, self.tests = list(gate), list(audit), dict(tests)
        self.out, self.config, self.proposer = Path(out), config, proposer
        self.sign = 1 if domain.higher_is_better else -1
        self.rng = random.Random(config.seed)
        self.seconds = {}
        self._rollout_cache = {}
        self._written = set()
        self._signals = {}

    # ---------------------------------------------------------------- helpers
    def _timed(self, kind, fn, *args, **kw):
        started = time.monotonic()
        try:
            return fn(*args, **kw)
        finally:
            self.seconds[kind] = self.seconds.get(kind, 0.0) + time.monotonic() - started

    def _clock(self):
        if time.monotonic() - self.started > self.config.wall_seconds:
            raise TimeoutError("application_wall_budget")

    def _score(self, version, cases, kind, evaluator=None):
        evaluator = evaluator or self.domain
        records = self._timed(kind, evaluator.evaluate, self.backend, version, cases)
        if [r.id for r in records] != [c.id for c in cases]:
            raise ValueError("evaluation_denominator_or_order")
        return _mean(records), records

    def _check_receipt(self, receipt, parent: Version, out_dir: Path, versions: set):
        if (receipt.version.parent_id != parent.id or receipt.version.id in versions
                or receipt.optimizer_steps <= 0 or receipt.trainable_parameters <= 0
                or receipt.before_sha256 == receipt.after_sha256
                or Path(receipt.version.location).resolve() != out_dir.resolve()
                or not out_dir.is_dir() or not any(out_dir.iterdir())):
            raise ValueError("unproven_or_mismatched_training_update")

    def _rollouts(self, generator, program, round_index, seed, heldout):
        params = program.params
        key = digest([generator.id, params.get("curriculum"), params.get("solver"),
                      round_index, seed])
        if key in self._rollout_cache:
            return self._rollout_cache[key]
        proposed = self._timed("propose", self.domain.propose, self.backend, generator,
                               params, round_index, seed)
        cases, rejected = [], dict(heldout_leak=0, duplicate=0)
        for case in proposed:
            k = self.domain.leakage_key(case)
            if case.split != "train":
                raise ValueError("proposed_cases_must_be_train")
            if k in heldout:
                rejected["heldout_leak"] += 1
            elif k in self._seen_train:
                rejected["duplicate"] += 1
            else:
                self._seen_train.add(k)
                cases.append(case)
        if not cases:
            raise ValueError("no_admissible_training_cases")
        attempts = self._timed("attempt", self.domain.attempt, self.backend, generator,
                               cases, params, seed)
        result = (cases, attempts, rejected)
        self._rollout_cache[key] = result
        return result

    # ------------------------------------------------------------------- run
    def run(self):
        cfg = self.config
        self.out.mkdir(parents=True, exist_ok=False)
        self.started = time.monotonic()
        heldout = {}
        for split, cases in (("gate", self.gate), ("audit", self.audit)):
            for c in cases:
                if c.split != split:
                    raise ValueError(f"{split}_split_required")
                heldout[self.domain.leakage_key(c)] = split
        for name, (suite, cases) in self.tests.items():
            for c in cases:
                if c.split != "test":
                    raise ValueError("test_split_required")
                heldout.setdefault(suite.leakage_key(c), f"test:{name}")
        plan = dict(protocol="rsi_two_level_v1", config=asdict(cfg), initial=asdict(self.initial),
                    seed_program=asdict(self.seed_program), domain=self.domain.name,
                    proposer=getattr(self.proposer, "name", type(self.proposer).__name__),
                    gate_ids=[c.id for c in self.gate], audit_ids=[c.id for c in self.audit],
                    tests={n: [c.id for c in cs] for n, (_, cs) in self.tests.items()},
                    test_role="read once after the last round; never decides anything")
        _write(self.out / "plan.json", plan)
        archive = Archive(self.out / "archive.jsonl")
        self._seen_train = set()
        versions = {self.initial.id}
        try:
            gate0, _ = self._score(self.initial, self.gate, "gate_eval")
            audit0, _ = self._score(self.initial, self.audit, "audit_eval")
            root = archive.add(Node("n0", 0, self.initial, self.seed_program, None,
                                    gate=gate0, audit=audit0, accepted=True))
            parent = root
            for r in range(1, cfg.rounds + 1):
                self._clock()
                seed = cfg.seed * 1000 + r
                programs = [parent.program]
                if cfg.candidates_per_round > 1:
                    proposed = self._timed("meta", self.proposer.propose, parent.program,
                                           archive, self.backend, parent.version,
                                           cfg.candidates_per_round - 1, self.rng)
                    for p in proposed:
                        p = Program.make(self.domain.validate_program(p.params),
                                         parent.program.id, p.author, p.note)
                        if p.id not in {q.id for q in programs}:
                            programs.append(p)
                generator = parent.version if cfg.recursive else self.initial
                candidates = []
                for k, program in enumerate(programs):
                    self._clock()
                    cases, attempts, rejected = self._rollouts(generator, program, r, seed, heldout)
                    if cfg.feedback == "shuffled":
                        attempts = shuffle_feedback(attempts, random.Random(seed * 31 + k))
                    items, item_cases, stats = curate(cases, attempts, program.params["curation"],
                                                      random.Random(seed * 17 + k))
                    tag = f"r{r:02d}c{k}"
                    rollout_id = digest([generator.id, program.params.get("curriculum"),
                                         program.params.get("solver"), r, seed])[:12]
                    if rollout_id not in self._signals:
                        self._signals[rollout_id] = self.domain.signal_metrics(cases, attempts)
                    signal = dict(self._signals[rollout_id], rejected=rejected,
                                  generator=generator.id)
                    if not items:
                        archive.add(Node(tag, r, parent.version, program, parent.node_id,
                                         signal=signal, curation=stats))
                        continue
                    if rollout_id not in self._written:
                        self._written.add(rollout_id)
                        _jsonl(self.out / f"round-{r:02d}-cases-{rollout_id}.jsonl",
                               [asdict(c) for c in cases])
                        _jsonl(self.out / f"round-{r:02d}-attempts-{rollout_id}.jsonl",
                               [asdict(a) for t in attempts for a in t])
                    signal["rollout_id"] = rollout_id
                    ckpt = self.out / f"ckpt-{tag}"
                    receipt = self._timed("train", self.backend.train, parent.version, items,
                                          ckpt, program.params["update"], seed * 7 + k)
                    self._check_receipt(receipt, parent.version, ckpt, versions)
                    versions.add(receipt.version.id)
                    gate, _ = self._score(receipt.version, self.gate, "gate_eval")
                    node = archive.add(Node(tag, r, receipt.version, program, parent.node_id,
                                            gate=gate, signal=signal, curation=stats,
                                            receipt=asdict(receipt),
                                            seconds=dict(self.seconds)))
                    candidates.append(node)
                best = max(candidates, key=lambda n: self.sign * n.gate, default=None)
                accepted = (best is not None and
                            self.sign * best.gate >= self.sign * parent.gate + cfg.min_gate_gain)
                if accepted:
                    best.accepted = True
                    best.audit, _ = self._score(best.version, self.audit, "audit_eval")
                    with (self.out / "accepted.jsonl").open("a") as s:
                        s.write(json.dumps(dict(round=r, node=best.node_id, gate=best.gate,
                                                audit=best.audit, program=best.program.id,
                                                author=best.program.author)) + "\n")
                    parent = best
                _write(self.out / f"round-{r:02d}.json", dict(
                    round=r, parent=parent.node_id, accepted=accepted,
                    candidates=[dict(node=n.node_id, gate=n.gate, program=n.program.id,
                                     author=n.program.author, curation=n.curation,
                                     signal=n.signal) for n in candidates],
                    seconds=dict(self.seconds)))
            # ---- sealed tests: only now, after every decision is frozen ----
            _write(self.out / "retained.json", dict(node=parent.node_id,
                                                    version=asdict(parent.version),
                                                    program=asdict(parent.program)))
            chain = [n for n in archive.nodes if n.accepted]
            if cfg.seal_tests:
                report = dict(status="complete_tests_sealed", config=asdict(cfg),
                              retained=parent.node_id,
                              accepted_chain=[dict(node=n.node_id, round=n.round, gate=n.gate,
                                                   audit=n.audit) for n in chain],
                              seconds=dict(self.seconds), elapsed=time.monotonic() - self.started)
                _write(self.out / "report.json", report)
                return report
            if not cfg.test_all_accepted:
                chain = [root, parent] if parent is not root else [root]
            tests = {}
            for name, (suite, cases) in self.tests.items():
                per_version = {}
                for node in chain:
                    self._clock()
                    score, records = self._score(node.version, cases, "test_eval", suite)
                    per_version[node.node_id] = (score, records)
                    _jsonl(self.out / f"test-{name}-{node.node_id}.jsonl",
                           [asdict(x) for x in records])
                from .stats import paired_report
                a = [x.score for x in per_version[root.node_id][1]]
                b = [x.score for x in per_version[parent.node_id][1]]
                tests[name] = dict(curve=[dict(node=n.node_id, round=n.round,
                                               score=per_version[n.node_id][0]) for n in chain],
                                   initial=per_version[root.node_id][0],
                                   final=per_version[parent.node_id][0],
                                   paired=paired_report(a, b, 1 if suite.higher_is_better else -1,
                                                        seed=cfg.seed))
            report = dict(status="complete", config=asdict(cfg), retained=parent.node_id,
                          accepted_chain=[dict(node=n.node_id, round=n.round, gate=n.gate,
                                               audit=n.audit, program=n.program.id,
                                               author=n.program.author) for n in chain],
                          tests=tests, seconds=dict(self.seconds),
                          elapsed=time.monotonic() - self.started)
            _write(self.out / "report.json", report)
            return report
        except Exception as exc:
            if not (self.out / "failure.json").exists():
                try:
                    _write(self.out / "failure.json", dict(status="failed",
                                                           error=type(exc).__name__,
                                                           message=str(exc)[:500]))
                except Exception:
                    pass
            raise
