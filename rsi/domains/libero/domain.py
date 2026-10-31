"""LIBERO manipulation domain for VLA policies; the simulator's success flag is the oracle.

Cases are (task, initial configuration). Training cases are *freshly sampled*
object placements chosen by the curriculum (how many per task, and how they
are allocated across tasks); gate/audit use disjoint blocks of sampled
placements; the test suite is the official benchmark - the 50 fixed initial
states of every task - so training never touches a benchmark state and the
test number is the standard LIBERO protocol.

An attempt is one episode, verified iff the environment reports success. The
experience is the saved episode: the frames the policy saw and the action
tokens it emitted. Curriculum allocation can follow learning progress: tasks
whose verified rate is neither ~0 nor ~1 get more practice.
"""

import copy

from ...core.types import Attempt, Case, EvalRecord

TRAIN_SEED_BASE = 100_000_000
HELDOUT_SEED_BASE = 900_000_000
FRESH_GATE_SEED_BASE = 950_000_000     # per-round gate sets of gate_mode fresh_paired; disjoint from the above

DEFAULT_PROGRAM = {
    "curriculum": {"cases": 160, "allocation": "uniform", "floor": 0.05},
    "solver": {"samples": 8, "temperature": 1.5, "greedy": 0},
    "curation": {"rule": "mixed_groups", "budget": 400, "per_case": 2, "band": [0.0, 1.0]},
    "update": {"operator": "grpo", "lr": 1e-5, "steps": 200, "batch": 64,
               "clip_low": 0.2, "clip_high": 0.28},
}

EDIT_SPACE = {
    "curriculum.cases": (40, 400), "curriculum.allocation": ["uniform", "progress"],
    "solver.samples": (4, 16), "solver.temperature": (1.0, 2.0),
    "curation.rule": ["mixed_groups", "verified"], "curation.budget": (40, 1000),
    "update.operator": ["grpo", "bc"], "update.lr": (2e-6, 1e-4),
    "update.steps": (50, 1500), "update.batch": (16, 128),
}

# Harness components (addendum 16): design choices of the improvement procedure itself, which a meta level with
# space "harness" may change in addition to the knobs above. The four OPTIONAL_FIELDS may be absent from a program;
# absent means the historical behaviour (the run's VLAConfig for ratio/loss_agg/bc_temp, a centred advantage).
OPTIONAL_FIELDS = {"update.ratio": ["legacy", "matched"], "update.loss_agg": ["token", "episode"],
                   "update.bc_temp": ["unit", "rollout"], "curation.adv": ["center", "zscore"]}
HARNESS_EXTRA = {"curation.band": [[0.0, 1.0], [0.1, 0.9], [0.2, 0.8], [0.3, 0.7]],
                 "curation.per_case": (1, 8), "curriculum.floor": (0.0, 0.3),
                 "update.clip_low": (0.1, 0.4), "update.clip_high": (0.1, 0.5)}
HARNESS_SPACE = dict(EDIT_SPACE, **HARNESS_EXTRA, **OPTIONAL_FIELDS)
# Neutral descriptions of every field for an LLM meta level: what each option computes, never which is better.
HARNESS_DOC = """Field meanings. curriculum.cases: scenes practised per update step. curriculum.allocation: 'uniform' spreads
scenes evenly over tasks; 'progress' gives more scenes to tasks whose recent tries had both outcomes.
curriculum.floor: minimum share of a task under 'progress'. solver.samples: tries per scene. solver.temperature:
sampling temperature of the tries. curation.rule: 'mixed_groups' keeps every try of scenes whose success fraction
lies strictly inside curation.band (used by grpo); 'verified' keeps successful tries only (used by bc).
curation.band: [lo, hi] success-fraction band of the scenes that are used. curation.per_case: at most this many
successful tries per scene (bc). curation.budget: at most this many scenes (grpo) or tries (bc) per step.
curation.adv: the per-try advantage in a scene is reward minus the scene mean ('center') or that divided by the
scene's standard deviation ('zscore'). update.operator: 'grpo' (clipped policy gradient with those advantages) or
'bc' (maximise the likelihood of the kept tries). update.lr, update.steps, update.batch: learning rate,
optimiser steps and batch size of one update.
update.clip_low, update.clip_high: clip range of the
policy ratio in grpo. update.ratio: the 'old' log-probabilities of
the ratio are computed in a separate pass over all items ('legacy') or on exactly the micro-batches that are
trained ('matched'). update.loss_agg: the loss averages over tokens ('token') or gives every episode the same total
weight ('episode'). update.bc_temp: bc's likelihood uses logits at temperature 1 ('unit') or divided by the
sampling temperature of the try ('rollout')."""

# Count fields whose upper bound grows with a run's budget_scale, so a compute-matched single round (`onebig`:
# the summed budget of N rounds at once) validates without widening the space the meta level searches.
BUDGET_FIELDS = ("curriculum.cases", "curation.budget", "update.steps")

COUPLING = {
    "update.operator": {"curation.rule": {"grpo": "mixed_groups", "bc": "verified"}},
    "curation.rule": {"update.operator": {"mixed_groups": "grpo", "verified": "bc"}},
}


def _get(params, dotted):
    node = params
    for key in dotted.split("."):
        node = node[key]
    return node


class LiberoDomain:
    name = "libero"
    higher_is_better = True

    def __init__(self, suite, tasks, budget_scale=1):
        self.suite, self.tasks = suite, list(tasks)
        self.budget_scale = budget_scale
        self.edit_space, self.coupling = EDIT_SPACE, COUPLING
        self.harness_space, self.harness_doc = HARNESS_SPACE, HARNESS_DOC
        self.task_rates = {t: None for t in self.tasks}   # latest verified rate per task

    def default_program(self):
        return copy.deepcopy(DEFAULT_PROGRAM)

    def validate_program(self, params):
        out = copy.deepcopy(DEFAULT_PROGRAM)
        for section, values in (params or {}).items():
            if section not in out or not isinstance(values, dict):
                raise ValueError(f"unknown_program_section:{section}")
            for key, value in values.items():
                if key not in out[section] and f"{section}.{key}" not in OPTIONAL_FIELDS:
                    raise ValueError(f"unknown_program_field:{section}.{key}")
                out[section][key] = value
        for dotted, allowed in OPTIONAL_FIELDS.items():
            section, key = dotted.split(".")
            if key in out[section] and out[section][key] not in allowed:
                raise ValueError(f"program_value_not_allowed:{dotted}")
        band = out["curation"]["band"]
        if not (isinstance(band, (list, tuple)) and len(band) == 2 and 0.0 <= band[0] < band[1] <= 1.0):
            raise ValueError("program_value_out_of_range:curation.band")
        for dotted, space in HARNESS_EXTRA.items():
            if isinstance(space, tuple):
                value = _get(out, dotted)
                if not isinstance(value, (int, float)) or not space[0] <= value <= space[1]:
                    raise ValueError(f"program_value_out_of_range:{dotted}")
        for dotted, space in EDIT_SPACE.items():
            value = _get(out, dotted)
            if isinstance(space, list):
                if value not in space:
                    raise ValueError(f"program_value_not_allowed:{dotted}")
            else:
                high = space[1] * (self.budget_scale if dotted in BUDGET_FIELDS else 1)
                if not isinstance(value, (int, float)) or not space[0] <= value <= high:
                    raise ValueError(f"program_value_out_of_range:{dotted}")
        pairs = {("grpo", "mixed_groups"), ("bc", "verified")}
        if (out["update"]["operator"], out["curation"]["rule"]) not in pairs:
            raise ValueError("operator_curation_mismatch")
        return out

    def leakage_key(self, case):
        i = case.inputs
        init = i["init"]
        return f"{self.suite}|{i['task_id']}|{init['kind']}|{init.get('index', init.get('seed'))}"

    def official_test(self, inits_per_task=50):
        return [Case(f"{self.suite}-t{t}-official{k}", f"{self.suite}-t{t}-official{k}", "test",
                     dict(task_id=t, init=dict(kind="official", index=k)),
                     f"libero:{self.suite}:task{t}:official{k}")
                for t in self.tasks for k in range(inits_per_task)]

    def heldout(self, per_task):
        out = []
        for t in self.tasks:
            for k in range(per_task):
                split = "gate" if k % 2 == 0 else "audit"
                s = HELDOUT_SEED_BASE + 1000 * t + k
                out.append(Case(f"{self.suite}-t{t}-{split}{k}", f"{self.suite}-t{t}-{split}{k}",
                                split, dict(task_id=t, init=dict(kind="random", seed=s)),
                                f"libero:{self.suite}:task{t}:sampled{s}"))
        return [c for c in out if c.split == "gate"], [c for c in out if c.split == "audit"]

    def _allocation(self, cur):
        n = int(cur["cases"])
        if cur["allocation"] == "uniform" or any(r is None for r in self.task_rates.values()):
            weights = {t: 1.0 for t in self.tasks}
        else:
            # learning progress proxy: practice where outcomes are mixed
            weights = {t: max(cur["floor"], r * (1 - r)) for t, r in self.task_rates.items()}
        total = sum(weights.values())
        counts = {t: max(1, round(n * w / total)) for t, w in weights.items()}
        return counts

    def fresh_gates(self, rounds, per_task):
        """{round: gate cases} for gate_mode fresh_paired: a new set of sampled placements each round."""
        out = {}
        for r in range(1, rounds + 1):
            out[r] = []
            for t in self.tasks:
                for k in range(per_task):
                    s = FRESH_GATE_SEED_BASE + 100_000 * r + 1000 * t + k
                    cid = f"{self.suite}-t{t}-fresh-r{r}-{k}"
                    out[r].append(Case(cid, cid, "gate", dict(task_id=t, init=dict(kind="random", seed=s)),
                                       f"libero:{self.suite}:task{t}:sampled{s}"))
        return out

    def propose(self, backend, generator, program, round_index, seed):
        out = []
        for t, count in self._allocation(program["curriculum"]).items():
            for k in range(count):
                s = TRAIN_SEED_BASE + seed * 1_000_000 + round_index * 10_000 + 100 * t + k
                if not 0 <= s < 2 ** 32:                     # LIBERO seeds numpy's legacy generator
                    raise ValueError(f"placement_seed_out_of_range:{s}")
                cid = f"{self.suite}-t{t}-r{round_index}-s{s}"
                out.append(Case(cid, cid, "train", dict(task_id=t, init=dict(kind="random", seed=s)),
                                f"libero:{self.suite}:task{t}:sampled{s}"))
        return out

    def attempt(self, backend, generator, cases, program, seed):
        sol = program["solver"]
        episodes = []
        for case in cases:
            for a in range(int(sol["samples"])):
                greedy = a < int(sol["greedy"])
                episodes.append(dict(id=f"{case.id}-a{a}", case_id=case.id,
                                     task_id=case.inputs["task_id"], init=case.inputs["init"],
                                     mode="greedy" if greedy else "sample",
                                     temperature=0.0 if greedy else float(sol["temperature"]),
                                     sample_seed=seed * 7919 + a, save=True))
        results = backend.rollout(generator, self.suite, episodes)
        by_case = {}
        for ep in results:
            by_case.setdefault(ep["case_id"], []).append(Attempt(
                ep["case_id"], float(ep["success"]), bool(ep["success"]),
                dict(episode=ep["path"], temperature=ep["temperature"]),
                dict(id=ep["id"], steps=ep["steps"], mode=ep["mode"])))
        attempts = [sorted(by_case[c.id], key=lambda a: a.details["id"]) for c in cases]
        per_task = {}
        for c, tries in zip(cases, attempts):
            per_task.setdefault(c.inputs["task_id"], []).extend(a.verified for a in tries)
        for t, v in per_task.items():
            self.task_rates[t] = sum(v) / len(v)
        return attempts

    def evaluate(self, backend, version, cases):
        episodes = [dict(id=c.id, case_id=c.id, task_id=c.inputs["task_id"], init=c.inputs["init"],
                         mode="greedy", temperature=0.0, sample_seed=0, save=False) for c in cases]
        results = {ep["id"]: ep for ep in backend.rollout(version, self.suite, episodes)}
        return [EvalRecord(c.id, float(results[c.id]["success"]), None,
                           dict(steps=results[c.id]["steps"])) for c in cases]

    def signal_metrics(self, cases, attempts):
        rates = [sum(a.verified for a in t) / len(t) for t in attempts]
        return dict(cases=len(cases), verified_rate=sum(rates) / len(rates),
                    mixed_fraction=sum(0 < r < 1 for r in rates) / len(rates),
                    unsolved_fraction=sum(r == 0 for r in rates) / len(rates),
                    task_rates=dict(self.task_rates))
