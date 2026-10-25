"""Meta-level proposers: who suggests changes to the improvement program.

All proposers work inside the domain's declared edit space and return
candidate programs; the engine runs each candidate for real and the gate set
decides. None of them can see test data or touch the oracle.

* ``FixedProgram``  - never proposes (the fixed-program control).
* ``NumericSearch`` - mutates declared knobs; prefers knobs whose past changes
                      raised the gate score (a simple credit-assignment bandit).
                      Works for any model, including VLAs.
* ``SelfEdit``      - the model being improved reads the archive summary and
                      rewrites its own improvement program (JSON). Invalid or
                      unparseable edits fall back to ``NumericSearch``.
"""

import copy
import json
import math
import re

from ..core.archive import program_diff
from ..core.types import Program


def _get(params, dotted):
    node = params
    for key in dotted.split("."):
        node = node[key]
    return node


def _put(params, dotted, value):
    node = params
    keys = dotted.split(".")
    for key in keys[:-1]:
        node = node[key]
    node[keys[-1]] = value


CODE_WM_COUPLING = {
    "update.operator": {"curation.rule": {"grpo": "mixed_groups", "sft": "verified"}},
    "curation.rule": {"update.operator": {"mixed_groups": "grpo", "verified": "sft"}},
}


class FixedProgram:
    name = "fixed"

    def propose(self, program, archive, backend, version, k, rng):
        return []


class NumericSearch:
    name = "numeric_search"

    def __init__(self, edit_space, validate, coupled=None):
        self.space, self.validate = edit_space, validate
        # knobs that must change together, e.g. switching operator also switches curation rule
        self.coupled = coupled or {}

    def _credit(self, archive):
        credit = {}
        for row in archive.summary(limit=64):
            if row["gate_gain"] is None:
                continue
            for knob in row["changes"]:
                credit.setdefault(knob, []).append(row["gate_gain"])
        return {k: sum(v) / len(v) for k, v in credit.items()}

    def _mutate(self, params, knob, rng):
        space = self.space[knob]
        value = _get(params, knob)
        if isinstance(space, list):
            choices = [c for c in space if c != value]
            new = rng.choice(choices) if choices else value
        else:
            lo, hi = space
            if isinstance(lo, int) and isinstance(hi, int):
                new = int(round(min(hi, max(lo, value * rng.choice([0.5, 0.75, 1.5, 2.0])))))
            elif lo > 0 and hi / lo > 20:          # log-scale knobs such as learning rate
                new = float(min(hi, max(lo, value * math.exp(rng.uniform(-1.2, 1.2)))))
            else:
                new = float(min(hi, max(lo, value + rng.uniform(-0.25, 0.25) * (hi - lo))))
        _put(params, knob, new)
        for other, mapping in self.coupled.get(knob, {}).items():
            if new in mapping:
                _put(params, other, mapping[new])

    def propose(self, program, archive, backend, version, k, rng):
        credit = self._credit(archive)
        knobs = list(self.space)
        weights = [math.exp(4.0 * credit.get(knob, 0.0) * 10) for knob in knobs]
        out, tries = [], 0
        while len(out) < k and tries < 50 * k:
            tries += 1
            params = copy.deepcopy(program.params)
            for _ in range(rng.choice([1, 1, 2])):
                knob = rng.choices(knobs, weights=weights)[0]
                self._mutate(params, knob, rng)
            try:
                params = self.validate(params)
            except ValueError:
                continue
            if params != program.params and all(params != p.params for p in out):
                out.append(Program.make(params, program.id, "search",
                                        json.dumps(program_diff(program.params, params))))
        return out


SELF_EDIT_PROMPT = """You are improving the procedure that trains you. Each round, the procedure below makes you write practice problems, solve them, keeps the solutions an external checker verifies, and updates your weights on them. A held-out gate score decides whether an update is kept.

Current procedure (JSON):
{program}

Allowed values (numbers are [min, max]; lists are the allowed choices):
{space}

History of past procedure changes and the gate score change each caused:
{history}

Propose ONE improved procedure. You may rewrite the "curriculum.instruction" text (it tells you what kind of practice problems to write) and change any allowed value. Answer with the complete JSON object only.
JSON:
"""


class SelfEdit:
    name = "self_edit"

    def __init__(self, edit_space, validate, fallback: NumericSearch, samples=8,
                 temperature=0.8, max_tokens=900):
        self.space, self.validate, self.fallback = edit_space, validate, fallback
        self.samples, self.temperature, self.max_tokens = samples, temperature, max_tokens
        self.log = []

    def propose(self, program, archive, backend, version, k, rng):
        space = {knob: v for knob, v in self.space.items()}
        history = json.dumps(archive.summary(limit=12), indent=1, default=str)[:3000]
        prompt = SELF_EDIT_PROMPT.format(program=json.dumps(program.params, indent=1),
                                         space=json.dumps(space), history=history)
        texts = backend.sample(version, [dict(prompt=prompt, n=self.samples,
                                              temperature=self.temperature, top_p=0.95,
                                              max_tokens=self.max_tokens, stop=None,
                                              seed=rng.randrange(1 << 30))])[0]
        out, reasons = [], {}
        for text in texts:
            match = re.search(r"\{.*\}", text, re.S)
            try:
                params = json.loads(match.group(0)) if match else None
                params = self.validate(params)
            except (ValueError, TypeError, AttributeError) as exc:
                key = type(exc).__name__ if not str(exc) else str(exc).split(":")[0]
                reasons[key] = reasons.get(key, 0) + 1
                continue
            if params != program.params and all(params != p.params for p in out):
                out.append(Program.make(params, program.id, "self",
                                        json.dumps(program_diff(program.params, params))))
            if len(out) >= k:
                break
        self.log.append(dict(samples=len(texts), valid=len(out), rejected=reasons))
        if len(out) < k:
            out += self.fallback.propose(program, archive, backend, version, k - len(out), rng)
        return out[:k]
