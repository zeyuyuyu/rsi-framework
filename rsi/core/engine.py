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
import re
import time

from .archive import Archive, Node
from .curation import curate, shuffle_feedback
from .types import Case, Program, Version, canonical, digest


@dataclass(frozen=True)
class EngineConfig:
    rounds: int = 3
    seed: int = 0
    recursive: bool = True
    feedback: str = "true"            # true | shuffled
    candidates_per_round: int = 1     # programs tried per round (incumbent included)
    inner_steps: int = 1              # on-policy sample -> curate -> train cycles per candidate before its gate
    min_gate_gain: float = 0.0
    # "fixed": every candidate is compared on the one gate set against its parent's stored gate score.
    # "fresh_paired": round r has its own gate set (``fresh_gates[r]``, never trained on); the parent is scored
    # on it again and the candidates are compared with that paired score, so acceptance cannot ratchet on one
    # set's noise (fixed-gate gains did not hold on the audit: addenda 7-8).
    gate_mode: str = "fixed"
    wall_seconds: int = 14 * 24 * 3600
    test_all_accepted: bool = True
    # Pilots (development decisions on the gate set) must not read test suites at all.
    seal_tests: bool = False
    # Meta level v2 (addendum 21): every candidate starts from the per-task rates its parent left (v3 let a candidate
    # read the rates its sibling's last inner step left), and nodes keep per-task gate success for the meta level.
    meta_v2: bool = False
    # Compute-matched fixed control (addendum 21): fill the round with copies of the incumbent program, so a fixed
    # arm trains as many children per round as a meta arm (they differ only in the training seed).
    replica_candidates: bool = False
    # Addendum 32 (guard-rail gate). None: off. With a number d (gate_mode fresh_paired only) the initial policy is
    # scored on every round's fresh gate set too, and a child must also reach initial_gate - d. Used with
    # min_gate_gain = -d the gate then refuses clear regressions (against the parent or against the start) instead
    # of discarding a round for a dip inside gate noise: on the 12-round Goal runs the strict gate threw away a
    # third of the rounds and the gated loop ended 2.7 points below ungated RL on fresh scenes (addendum 30, FL5).
    gate_floor: float | None = None


INNER_SEED_EXT_BASE = 4000     # rounds 10-12 (addendum 27): above run seed 3's block, below LIBERO's limit (seed < 4194)


def inner_seed(run_seed: int, round_index: int, step: int) -> int:
    """Seed of on-policy step ``step`` of round ``round_index``. Step 0 keeps the round seed (run_seed * 1000 +
    round), so inner_steps=1 runs are unchanged. Later steps use run_seed * 1000 + 100 * round + step: the same
    values as the first formula (round seed * 100 + step) for run seed 0, but small enough for seeds 1-3, where
    round seed * 100 sent LIBERO placement seeds (1e8 + seed * 1e6) past 2**32 and crashed the rollout workers
    (A800 pilot-6 replica, 10-30). Distinct for every (run seed, round <= 9, step <= 99).
    Rounds 10-12 (addendum 27, 12-round runs; the 11-07 launch failed on the old range check) take steps 1-15 of
    run seeds 0-3 from a block above every <= 9-round value: 4000 + 48 * seed + 16 * (round - 10) + step <= 4191,
    which keeps the largest LIBERO placement seed (1e8 + 4191e6 + 12e4 + 999) under 2**32. Rounds <= 9 and step 0
    are unchanged, so no finished run's placements move."""
    if step == 0:
        return run_seed * 1000 + round_index
    if 0 < step < 100 and 0 < round_index < 10:
        return run_seed * 1000 + 100 * round_index + step
    if 0 <= run_seed <= 3 and 10 <= round_index <= 12 and 0 < step < 16:
        return INNER_SEED_EXT_BASE + 48 * run_seed + 16 * (round_index - 10) + step
    raise ValueError(f"inner_seed_out_of_range:seed={run_seed},round={round_index},step={step}")


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



def _per_task(cases, records):
    """Per-task mean score of an evaluation, keyed by the case's task id (meta_v2 history for the meta level)."""
    out = {}
    for c, rec in zip(cases, records):
        out.setdefault(str(c.inputs.get("task_id")), []).append(rec.score)
    return {t: round(sum(v) / len(v), 4) for t, v in sorted(out.items())}

class Engine:
    def __init__(self, domain, backend, initial: Version, seed_program: dict, *,
                 gate, audit, tests: dict, out: Path, config: EngineConfig, proposer, fresh_gates=None):
        if config.gate_mode not in ("fixed", "fresh_paired"):
            raise ValueError(f"unknown_gate_mode:{config.gate_mode}")
        if (config.gate_mode == "fresh_paired") != (fresh_gates is not None):
            raise ValueError("fresh_gates_iff_fresh_paired")
        if config.gate_floor is not None and config.gate_mode != "fresh_paired":
            raise ValueError("gate_floor_needs_fresh_paired")
        if fresh_gates is not None:
            if sorted(fresh_gates) != list(range(1, config.rounds + 1)):
                raise ValueError("fresh_gates_must_cover_every_round")
            if any(c.split != "gate" for cs in fresh_gates.values() for c in cs):
                raise ValueError("gate_split_required")
        self.fresh_gates = {r: list(cs) for r, cs in fresh_gates.items()} if fresh_gates else None
        if config.inner_steps > 1 and not ((config.rounds <= 9 and config.inner_steps <= 99) or
                                           (config.rounds <= 12 and config.inner_steps <= 16 and 0 <= config.seed <= 3)):
            raise ValueError("inner_steps_need_rounds<=9_and_steps<=99_or_rounds<=12_steps<=16_seed<=3")  # inner_seed's range
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
        self._rates_after = {}   # node -> per-task rates after its last inner step (meta_v2)

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

    def _rollouts(self, generator, program, round_index, seed, heldout, exclude=frozenset()):
        params = program.params
        key = digest([generator.id, params.get("curriculum"), params.get("solver"),
                      round_index, seed])
        if key in self._rollout_cache:
            return self._rollout_cache[key]
        proposed = self._timed("propose", self.domain.propose, self.backend, generator,
                               params, round_index, seed)
        # Cases from earlier rounds are never reused; candidates of the same round may share cases (a
        # candidate that only edits the solver re-proposes the round's placements and must still train).
        prior = getattr(self, "_seen_before_round", self._seen_train)
        cases, local, rejected = [], set(), dict(heldout_leak=0, duplicate=0)
        for case in proposed:
            k = self.domain.leakage_key(case)
            if case.split != "train":
                raise ValueError("proposed_cases_must_be_train")
            if k in heldout:
                rejected["heldout_leak"] += 1
            elif k in prior or k in exclude or k in local:
                rejected["duplicate"] += 1
            else:
                local.add(k)
                cases.append(case)
        self._seen_train |= local
        if not cases:
            raise ValueError("no_admissible_training_cases")
        attempts = self._timed("attempt", self.domain.attempt, self.backend, generator,
                               cases, params, seed)
        result = (cases, attempts, rejected)
        self._rollout_cache[key] = result
        return result

    # ------------------------------------------------------------------- run
    def _restore(self, archive, versions):
        """Continue a run stopped between or inside rounds (e.g. a job wall-time kill). Completed
        rounds (round-NN.json written) are kept; whatever an unfinished round left behind is moved
        to resume-NN/, and the loop state is rebuilt from the files. Two things cannot be replayed
        and are recorded in resume.json: the meta proposer's random stream is re-seeded from
        (seed, completed rounds), and training cases of a candidate that curated no items were
        never written, so they do not enter the duplicate filter."""
        if (self.out / "report.json").exists():
            raise ValueError("run_already_complete")
        done = 0
        while (self.out / f"round-{done + 1:02d}.json").exists():
            done += 1
        aside, k = self.out / f"resume-{done + 1:02d}", 1
        while aside.exists():
            k += 1
            aside = self.out / f"resume-{done + 1:02d}-{k}"
        aside.mkdir()
        moved = []
        for path in sorted(self.out.iterdir()):
            name = path.name
            m = re.match(r"(?:round-|ckpt-r)(\d{2})", name)
            if (m and int(m.group(1)) > done) or name in ("failure.json", "retained.json") \
                    or name.startswith("test-"):
                path.rename(aside / name)
                moved.append(name)
        log = self.out / "archive.jsonl"
        rows = [json.loads(l) for l in log.read_text().splitlines() if l.strip()] if log.exists() else []
        kept, events = {}, []
        for row in rows:
            if row.get("event") == "accepted":
                events.append(row)
            elif row["round"] <= done:
                kept[row["node_id"]] = Node(**dict(row, version=Version(**row["version"]),
                                                   program=Program(**row["program"])))
        for event in events:
            if event["node_id"] in kept:
                node = kept[event["node_id"]]
                node.accepted, node.audit, node.gate = True, event["audit"], event["gate"]
        for name in ("archive.jsonl", "accepted.jsonl"):
            if (self.out / name).exists():
                (self.out / name).rename(aside / name)
                moved.append(name)
        for node in kept.values():
            archive.add(node)
            if node.accepted and node.node_id != "n0":
                archive.mark_accepted(node)
                with (self.out / "accepted.jsonl").open("a") as s:
                    s.write(json.dumps(dict(round=node.round, node=node.node_id, gate=node.gate,
                                            audit=node.audit, program=node.program.id,
                                            author=node.program.author)) + "\n")
            versions.add(node.version.id)
        root = kept.get("n0")
        if root is None:
            gate0, _ = self._score(self.initial, self.gate, "gate_eval")
            audit0, _ = self._score(self.initial, self.audit, "audit_eval")
            root = archive.add(Node("n0", 0, self.initial, self.seed_program, None,
                                    gate=gate0, audit=audit0, accepted=True))
        accepted = [n for n in kept.values() if n.accepted]
        parent = max(accepted, key=lambda n: n.round) if accepted else root
        for path in sorted(self.out.glob("round-*-cases-*.jsonl")):
            for line in path.read_text().splitlines():
                if line.strip():
                    self._seen_train.add(self.domain.leakage_key(Case(**json.loads(line))))
        if done:
            self.seconds = dict(json.loads((self.out / f"round-{done:02d}.json").read_text())["seconds"])
        self.rng = random.Random(self.config.seed * 1_000_003 + done)
        record = dict(at=time.time(), completed_rounds=done, parent=parent.node_id, set_aside=moved,
                      seen_train=len(self._seen_train), meta_rng=f"reseeded seed*1000003+{done}")
        with (self.out / "resume.json").open("a") as s:
            s.write(json.dumps(record) + "\n")
        return root, parent, done

    def run(self, resume=False):
        cfg = self.config
        if not resume:
            self.out.mkdir(parents=True, exist_ok=False)
        self.started = time.monotonic()
        heldout = {}
        for split, cases in (("gate", self.gate), ("audit", self.audit)):
            for c in cases:
                if c.split != split:
                    raise ValueError(f"{split}_split_required")
                heldout[self.domain.leakage_key(c)] = split
        for r, cases in (self.fresh_gates or {}).items():
            for c in cases:
                heldout.setdefault(self.domain.leakage_key(c), f"gate_fresh:{r}")
        for name, (suite, cases) in self.tests.items():
            for c in cases:
                if c.split != "test":
                    raise ValueError("test_split_required")
                heldout.setdefault(suite.leakage_key(c), f"test:{name}")
        plan_config = asdict(cfg)
        if plan_config.get("gate_floor") is None:      # absent when off, so runs made before addendum 32 still resume
            plan_config.pop("gate_floor", None)
        plan = dict(protocol="rsi_two_level_v1", config=plan_config, initial=asdict(self.initial),
                    seed_program=asdict(self.seed_program), domain=self.domain.name,
                    proposer=getattr(self.proposer, "name", type(self.proposer).__name__),
                    gate_ids=[c.id for c in self.gate], audit_ids=[c.id for c in self.audit],
                    tests={n: [c.id for c in cs] for n, (_, cs) in self.tests.items()},
                    **({"fresh_gate_ids": {str(r): [c.id for c in cs] for r, cs in self.fresh_gates.items()}}
                       if self.fresh_gates else {}),
                    test_role="read once after the last round; never decides anything")
        if resume:
            stored = json.loads((self.out / "plan.json").read_text())
            if stored != json.loads(json.dumps(plan, sort_keys=True, default=str)):
                raise ValueError("resume_plan_mismatch")
        else:
            _write(self.out / "plan.json", plan)
        archive = Archive(self.out / "archive.jsonl")
        self._seen_train = set()
        versions = {self.initial.id}
        try:
            if resume:
                root, parent, done = self._restore(archive, versions)
            else:
                gate0, _ = self._score(self.initial, self.gate, "gate_eval")
                audit0, _ = self._score(self.initial, self.audit, "audit_eval")
                root = archive.add(Node("n0", 0, self.initial, self.seed_program, None,
                                        gate=gate0, audit=audit0, accepted=True))
                parent, done = root, 0
            for r in range(done + 1, cfg.rounds + 1):
                self._clock()
                self._seen_before_round = frozenset(self._seen_train)
                seed = cfg.seed * 1000 + r
                rates0 = dict(self._rates_after.get(parent.node_id, self.domain.task_rates)) \
                    if cfg.meta_v2 and hasattr(self.domain, "task_rates") else None
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
                if cfg.replica_candidates:
                    programs += [parent.program] * (cfg.candidates_per_round - len(programs))
                generator = parent.version if cfg.recursive else self.initial
                candidates = []
                gate_cases, parent_gate, parent_tasks = self.gate, None, None
                if self.fresh_gates:
                    gate_cases = self.fresh_gates[r]
                    parent_gate, precs = self._score(parent.version, gate_cases, "gate_eval")
                    parent_tasks = _per_task(gate_cases, precs) if cfg.meta_v2 else None
                initial_gate = None
                if cfg.gate_floor is not None:
                    initial_gate = parent_gate if parent is root else \
                        self._score(self.initial, gate_cases, "gate_eval")[0]
                for k, program in enumerate(programs):
                    tag = f"r{r:02d}c{k}"
                    if rates0 is not None:
                        self.domain.task_rates = dict(rates0)
                    version, used, steps, signal, stats, receipt = parent.version, set(), [], None, None, None
                    for it in range(cfg.inner_steps):
                        self._clock()
                        s_it = inner_seed(cfg.seed, r, it)
                        gen = (version if it else generator) if cfg.recursive else self.initial
                        cases, attempts, rejected = self._rollouts(gen, program, r, s_it, heldout,
                                                                   exclude=frozenset(used))
                        used |= {self.domain.leakage_key(c) for c in cases}
                        if cfg.feedback == "shuffled":
                            attempts = shuffle_feedback(attempts, random.Random(s_it * 31 + k))
                        items, item_cases, step_stats = curate(cases, attempts, program.params["curation"],
                                                               random.Random(s_it * 17 + k))
                        rollout_id = digest([gen.id, program.params.get("curriculum"),
                                             program.params.get("solver"), r, s_it])[:12]
                        if rollout_id not in self._signals:
                            self._signals[rollout_id] = self.domain.signal_metrics(cases, attempts)
                        step_signal = dict(self._signals[rollout_id], rejected=rejected, generator=gen.id,
                                           rollout_id=rollout_id)
                        if signal is None:
                            signal, stats = dict(step_signal), step_stats
                        if not items:
                            steps.append(dict(step=it, signal=step_signal, curation=step_stats, trained=False))
                            break
                        if rollout_id not in self._written:
                            self._written.add(rollout_id)
                            _jsonl(self.out / f"round-{r:02d}-cases-{rollout_id}.jsonl",
                                   [asdict(c) for c in cases])
                            _jsonl(self.out / f"round-{r:02d}-attempts-{rollout_id}.jsonl",
                                   [asdict(a) for t in attempts for a in t])
                        last = it == cfg.inner_steps - 1
                        ckpt = self.out / (f"ckpt-{tag}" if last else f"ckpt-{tag}-i{it}")
                        step_receipt = self._timed("train", self.backend.train, version, items, ckpt,
                                                   program.params["update"], s_it * 7 + k)
                        self._check_receipt(step_receipt, version, ckpt, versions)
                        versions.add(step_receipt.version.id)
                        version, receipt = step_receipt.version, step_receipt
                        steps.append(dict(step=it, signal=step_signal, curation=step_stats, trained=True,
                                          version=step_receipt.version.id))
                    if cfg.inner_steps > 1:
                        signal["inner"] = steps
                        final = self.out / f"ckpt-{tag}"
                        if receipt is not None and not final.exists():   # chain stopped early: no mixed groups
                            final.symlink_to(Path(receipt.version.location).name)
                    if receipt is None:
                        archive.add(Node(tag, r, parent.version, program, parent.node_id,
                                         signal=signal, curation=stats))
                        continue
                    gate, grecs = self._score(receipt.version, gate_cases, "gate_eval")
                    if cfg.meta_v2:
                        if hasattr(self.domain, "task_rates"):
                            self._rates_after[tag] = dict(self.domain.task_rates)
                        signal = dict(signal, gate_tasks=_per_task(gate_cases, grecs),
                                      parent_gate_tasks=parent_tasks)
                    node = archive.add(Node(tag, r, receipt.version, program, parent.node_id,
                                            gate=gate, parent_gate=parent_gate, signal=signal, curation=stats,
                                            receipt=asdict(receipt),
                                            seconds=dict(self.seconds)))
                    candidates.append(node)
                best = max(candidates, key=lambda n: self.sign * n.gate, default=None)
                bar = parent.gate if parent_gate is None else parent_gate
                accepted = (best is not None and
                            self.sign * best.gate >= self.sign * bar + cfg.min_gate_gain)
                if accepted and initial_gate is not None:      # guard rail against slow drift below the start
                    accepted = self.sign * best.gate >= self.sign * initial_gate - cfg.gate_floor
                if accepted:
                    best.audit, _ = self._score(best.version, self.audit, "audit_eval")
                    archive.mark_accepted(best)
                    with (self.out / "accepted.jsonl").open("a") as s:
                        s.write(json.dumps(dict(round=r, node=best.node_id, gate=best.gate,
                                                audit=best.audit, program=best.program.id,
                                                author=best.program.author)) + "\n")
                    parent = best
                _write(self.out / f"round-{r:02d}.json", dict(
                    round=r, parent=parent.node_id, accepted=accepted,
                    **({"parent_gate": parent_gate} if parent_gate is not None else {}),
                    **({"initial_gate": initial_gate} if initial_gate is not None else {}),
                    candidates=[dict(node=n.node_id, gate=n.gate, program=n.program.id,
                                     author=n.program.author, curation=n.curation,
                                     signal=n.signal) for n in candidates],
                    seconds=dict(self.seconds)))
                # a rejected candidate is never served or tested again; the backend may free what only serving
                # needed (merged full weights: 64 GB per candidate for a 32B model)
                release = getattr(self.backend, "release", None)
                if release:
                    for n in candidates:
                        if not n.accepted:
                            release(n.version)
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
