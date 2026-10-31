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


LLM_META_PROMPT = """You tune the training procedure of a robot policy that improves itself in simulation.

Each round, the current policy practises on fresh random scenes: curriculum.cases scenes, solver.samples tries each,
sampled at solver.temperature. A simulator marks every try success or failure, and that is the only feedback. Curation
picks the training items: "mixed_groups" (scenes with both outcomes; used with operator "grpo") or "verified" (successful
tries; used with operator "bc"). The update then trains the policy (operator, lr, steps, batch). A round runs this
practise-and-update loop a few times, each time with the newest policy. A gate score, the greedy success rate on unseen
scenes, decides whether a round's new policy is kept and passed on.

Current procedure (JSON):
{program}

Allowed values (numbers are [min, max]; lists are the allowed choices; grpo needs mixed_groups, bc needs verified):
{space}

History, oldest first. For each candidate: the fields that differed from its parent's procedure, its gate score and the
change against its parent, whether it was kept, and training-side signals per inner step (sampled success rate,
share of scenes with both outcomes, number of training items) plus the training loss at the first and last update step:
{history}

First diagnose in one or two sentences what limits improvement, for example too few scenes with both outcomes, sampled
success collapsing, a loss that keeps rising, or a gate that does not move. Then propose {k} DIFFERENT procedures to try
next. Change only allowed fields. Answer with JSON only:
{{"diagnosis": "...", "proposals": [{{"why": "<one sentence>", "procedure": <complete procedure JSON>}}, ...]}}"""


def llm_history(archive, limit=12):
    """Round history for the LLM meta-proposer: program changes, gate, acceptance and training-side signals.
    Audit scores and test results are never included."""
    rows = []
    for n in archive.nodes[-limit:]:
        parent = archive.get(n.parent_node) if n.parent_node else None
        gain = None if parent is None or n.gate is None or parent.gate is None \
            else n.gate - (parent.gate if n.parent_gate is None else n.parent_gate)
        steps = n.signal.get("inner") or [dict(signal=n.signal, curation=n.curation)]
        inner = []
        for st in steps:
            cur, sig = st.get("curation") or {}, st.get("signal") or {}
            att = cur.get("attempts")
            inner.append(dict(sampled_success=None if not att else round(cur.get("verified_attempts", 0) / att, 3),
                              mixed_share=None if sig.get("mixed_fraction") is None
                              else round(sig["mixed_fraction"], 3),
                              items=cur.get("items")))
        extra = (n.receipt or {}).get("extra") or {}
        rows.append(dict(round=n.round, node=n.node_id, author=n.program.author,
                         changes=program_diff(parent.program.params if parent else {}, n.program.params),
                         gate=n.gate, gate_change=None if gain is None else round(gain, 4), kept=n.accepted,
                         inner=inner, loss_first=extra.get("loss_first"), loss_last=extra.get("loss_last")))
    return rows


class OpenAICompatClient:
    """Minimal chat-completions client (stdlib only). The key is read from a file and never logged."""

    def __init__(self, base_url, model, key_file, timeout=180, retries=3):
        self.base_url, self.model, self.key_file = base_url.rstrip("/"), model, key_file
        self.timeout, self.retries = timeout, retries

    def __call__(self, prompt, temperature, max_tokens):
        import time
        import urllib.request
        from pathlib import Path
        key = Path(self.key_file).expanduser().read_text().strip()
        body = json.dumps(dict(model=self.model, messages=[dict(role="user", content=prompt)],
                               temperature=temperature, max_tokens=max_tokens)).encode()
        last = None
        for attempt in range(self.retries):
            try:
                req = urllib.request.Request(f"{self.base_url}/chat/completions", data=body, headers={
                    "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    out = json.loads(r.read())
                return out["choices"][0]["message"]["content"], out.get("usage") or {}
            except Exception as exc:              # network or gateway error: retry, then let the caller fall back
                last = exc
                time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"llm_call_failed:{type(last).__name__}")


class LLMMetaProposer:
    """Meta level driven by an external LLM: reads the round history (training-side signals, gate scores; never audit
    or test), diagnoses what limits improvement and proposes k procedures inside the declared edit space. Invalid or
    failed proposals fall back to ``NumericSearch``. Every call is logged (prompt digest, reply, usage)."""
    name = "llm_meta"

    def __init__(self, edit_space, validate, fallback: NumericSearch, client, model, log_path=None,
                 max_calls=24, temperature=1.0, max_tokens=4000):
        self.space, self.validate, self.fallback, self.client = edit_space, validate, fallback, client
        self.model, self.log_path, self.max_calls = model, log_path, max_calls
        self.temperature, self.max_tokens, self.calls = temperature, max_tokens, 0

    def prompt(self, program, archive, k):
        return LLM_META_PROMPT.format(program=json.dumps(program.params, indent=1, sort_keys=True),
                                      space=json.dumps(self.space), k=k,
                                      history=json.dumps(llm_history(archive), indent=1, default=str)[:12000])

    def _log(self, row):
        if self.log_path:
            with open(self.log_path, "a") as s:
                s.write(json.dumps(row, default=str) + "\n")

    def propose(self, program, archive, backend, version, k, rng):
        import hashlib
        out, rejected, reply, diagnosis = [], {}, None, None
        prompt = self.prompt(program, archive, k)
        if self.calls < self.max_calls:
            self.calls += 1
            try:
                reply, usage = self.client(prompt, self.temperature, self.max_tokens)
                match = re.search(r"\{.*\}", reply, re.S)
                data = json.loads(match.group(0)) if match else {}
                diagnosis = str(data.get("diagnosis", ""))[:500]
                for prop in data.get("proposals") or []:
                    try:
                        params = self.validate(prop.get("procedure"))
                    except (ValueError, TypeError, AttributeError) as exc:
                        key = str(exc).split(":")[0] or type(exc).__name__
                        rejected[key] = rejected.get(key, 0) + 1
                        continue
                    outside = sorted(set(program_diff(program.params, params)) - set(self.space))
                    if outside:                   # same knobs as numeric search, nothing else
                        rejected["outside_edit_space"] = rejected.get("outside_edit_space", 0) + 1
                        continue
                    if params != program.params and all(params != p.params for p in out):
                        note = json.dumps(dict(why=str(prop.get("why", ""))[:300],
                                               diff=program_diff(program.params, params)))
                        out.append(Program.make(params, program.id, "llm", note))
                    if len(out) >= k:
                        break
            except (RuntimeError, ValueError, TypeError, AttributeError) as exc:
                rejected["call_or_parse"] = str(exc)[:120]
                usage = {}
        else:
            usage = {}
            rejected["call_cap"] = self.max_calls
        n_llm = len(out)
        if len(out) < k:
            out += self.fallback.propose(program, archive, backend, version, k - len(out), rng)
        self._log(dict(model=self.model, prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                       prompt_chars=len(prompt), reply=reply, diagnosis=diagnosis, usage=usage,
                       llm_programs=n_llm, fallback_programs=len(out) - n_llm, rejected=rejected))
        return out[:k]
