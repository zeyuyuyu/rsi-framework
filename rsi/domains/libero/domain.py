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
# Sealed fresh-scene test (addendum 30): sampled placements no run has trained on, gated on or audited. A training
# seed is TRAIN_SEED_BASE + S * 1e6 + round * 1e4 + 100 * task + k with an offset inside its 1e6 block of at most
# 120,999; held-out seeds sit at offsets below 40,000 of block 900 and fresh gates in blocks 950-951. Offsets from
# 500,000 of block 970 are therefore used by nothing else.
FRESH_TEST_SEED_BASE = 970_500_000

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

BUDGET_DOC = """Compute cap: a procedure may not do more work per update step than the starting procedure.
curriculum.cases x solver.samples must stay at or below {rollouts} tries, and update.steps x update.batch at or
below {updates} examples. A procedure over the cap is scaled down (fewer scenes, then fewer tries; fewer steps, then
a smaller batch), so spend the budget where it helps most."""

# Meta level v2 (addendum 21): per-task allocation. curriculum.task_weights is a list with one weight per task (in the
# domain's task order); allocation "weights" splits curriculum.cases in proportion to it (weight 0 = no scenes).
# Only a domain built with v2=True accepts it, so v3 programs validate exactly as before.
TASK_WEIGHT_RANGE = (0.0, 4.0)
V2_EXTRA = {"curriculum.allocation": ["uniform", "progress", "weights"],
            "curriculum.task_weights": f"list of one number per task in [{TASK_WEIGHT_RANGE[0]}, {TASK_WEIGHT_RANGE[1]}]"}
# v2 lower bounds: under the seed cap (64 x 8 tries, 100 x 64 examples) a proposal that wants more tries per scene or a
# bigger batch must go below v3's 40 scenes / 50 steps (16 tries -> 32 scenes); the smoke run's LLM did exactly that
# and was rejected, so v2 widens the two lower bounds instead of discarding in-budget reallocations.
V2_BOUNDS = {"curriculum.cases": (16, 400), "update.steps": (25, 1500)}
V2_SPACE = dict(HARNESS_SPACE, **V2_EXTRA, **V2_BOUNDS)
V2_DOC = HARNESS_DOC + """
curriculum.allocation 'weights': scenes are split over tasks in proportion to curriculum.task_weights (one weight per
task, in task order; 0 gives a task no scenes this round); 'uniform' and 'progress' ignore task_weights."""

BUDGET_DOC_V2 = """Compute cap: a procedure may not do more work per update step than the starting procedure.
curriculum.cases x solver.samples must stay at or below {rollouts} tries, and update.steps x update.batch at or
below {updates} examples. A procedure over the cap is shrunk proportionally (scenes and tries by the same factor;
steps and batch by the same factor), so choose how to split the budget yourself."""

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


def _put(params, dotted, value):
    section, key = dotted.split(".")
    params[section][key] = value


class LiberoDomain:
    name = "libero"
    higher_is_better = True

    def __init__(self, suite, tasks, budget_scale=1, v2=False):
        self.suite, self.tasks = suite, list(tasks)
        self.budget_scale, self.v2 = budget_scale, v2
        self.v2_space, self.v2_doc = V2_SPACE, V2_DOC
        self.edit_space, self.coupling = EDIT_SPACE, COUPLING
        self.harness_space, self.harness_doc = HARNESS_SPACE, HARNESS_DOC
        self.task_rates = {t: None for t in self.tasks}   # latest verified rate per task
        self.budget_cap = None

    def default_program(self):
        return copy.deepcopy(DEFAULT_PROGRAM)

    def set_budget_cap(self, program):
        """Addendum 19: cap every procedure at the seed program's per-inner-step work, so the meta level can reallocate
        compute (scenes vs tries, steps vs batch) but not buy more of it."""
        p = self.validate_program(program)
        self.budget_cap = dict(rollouts=p["curriculum"]["cases"] * p["solver"]["samples"],
                               updates=p["update"]["steps"] * p["update"]["batch"])
        return (BUDGET_DOC_V2 if self.v2 else BUDGET_DOC).format(**self.budget_cap)

    def fit_budget(self, params):
        """Scale an over-cap procedure down onto the cap: fewer scenes, then fewer tries; fewer steps, then a smaller
        batch. Every other field is kept."""
        if not self.budget_cap:
            return params
        out = copy.deepcopy(params)
        if self.v2:
            return self._fit_proportional(out)
        for (count, per), cap in ((("curriculum.cases", "solver.samples"), self.budget_cap["rollouts"]),
                                  (("update.steps", "update.batch"), self.budget_cap["updates"])):
            if _get(out, count) * _get(out, per) > cap:
                _put(out, count, max(EDIT_SPACE[count][0], cap // _get(out, per)))
            if _get(out, count) * _get(out, per) > cap:
                _put(out, per, max(EDIT_SPACE[per][0], cap // _get(out, count)))
        return out

    def _fit_proportional(self, out):
        """v2 cap: shrink both factors of an over-cap product by the same factor, so the split the proposal chose
        (e.g. fewer scenes with more tries each) survives; v3 cut scenes first."""
        for (count, per), cap in ((("curriculum.cases", "solver.samples"), self.budget_cap["rollouts"]),
                                  (("update.steps", "update.batch"), self.budget_cap["updates"])):
            a, b = _get(out, count), _get(out, per)
            lo_a, lo_b = V2_BOUNDS.get(count, EDIT_SPACE[count])[0], EDIT_SPACE[per][0]
            if a * b > cap:
                f = (cap / (a * b)) ** 0.5
                a = max(lo_a, int(a * f))
                b = max(lo_b, int(b * f))
                while a * b > cap and a > lo_a:
                    a -= 1
                while a * b > cap and b > lo_b:
                    b -= 1
                _put(out, count, a)
                _put(out, per, b)
        return out

    def validate_capped(self, params):
        return self.fit_budget(self.validate_program(params))

    def validate_program(self, params):
        out = copy.deepcopy(DEFAULT_PROGRAM)
        for section, values in (params or {}).items():
            if section not in out or not isinstance(values, dict):
                raise ValueError(f"unknown_program_section:{section}")
            for key, value in values.items():
                v2_field = self.v2 and f"{section}.{key}" == "curriculum.task_weights"
                if key not in out[section] and f"{section}.{key}" not in OPTIONAL_FIELDS and not v2_field:
                    raise ValueError(f"unknown_program_field:{section}.{key}")
                out[section][key] = value
        cur = out["curriculum"]
        if self.v2 and cur["allocation"] == "weights":
            w = cur.get("task_weights")
            if not (isinstance(w, list) and len(w) == len(self.tasks)
                    and all(isinstance(x, (int, float)) and TASK_WEIGHT_RANGE[0] <= x <= TASK_WEIGHT_RANGE[1] for x in w)
                    and sum(w) > 0):
                raise ValueError("program_value_out_of_range:curriculum.task_weights")
            cur = dict(cur, allocation="uniform")      # the generic check below knows only uniform|progress
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
            space = V2_BOUNDS.get(dotted, space) if self.v2 else space
            value = cur["allocation"] if dotted == "curriculum.allocation" else _get(out, dotted)
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

    def fresh_test(self, per_task=100):
        """Sealed fresh-scene test (addendum 30): per_task sampled placements per task, the same for every run."""
        if not 0 < per_task <= 1000:
            raise ValueError("fresh_test_per_task_out_of_range")
        out = []
        for t in self.tasks:
            for k in range(per_task):
                s = FRESH_TEST_SEED_BASE + 1000 * t + k
                cid = f"{self.suite}-t{t}-freshtest{k}"
                out.append(Case(cid, cid, "test", dict(task_id=t, init=dict(kind="random", seed=s)),
                                f"libero:{self.suite}:task{t}:sampled{s}"))
        return out

    def _allocation(self, cur):
        n = int(cur["cases"])
        if self.v2 and cur["allocation"] == "weights":
            w = dict(zip(self.tasks, cur["task_weights"]))
            total = sum(w.values())
            return {t: (max(1, round(n * x / total)) if x > 0 else 0) for t, x in w.items()}
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
