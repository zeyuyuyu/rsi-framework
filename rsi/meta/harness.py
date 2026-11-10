"""Meta level v3 (addendum 29): a harness around the meta-level LLM.

v1/v2 gave the LLM one prompt per round holding a truncated summary of the round history, and nothing carried over
between rounds or between runs. v3 follows what recent outer-loop systems give their proposers (Meta-Harness: every
prior candidate reachable as files instead of a compressed summary; EvoTrainer: layered diagnostics and a persistent
memory that keeps negative evidence; LLMZero: diagnose the training signals, then change several fields together):

* a workspace of files: every candidate of this run (procedure, change against its parent, gate against the parent
  overall and per task, training-side signals of every inner step), an overview, a per-task table and an evidence
  ledger (gate changes pooled per edited field);
* a memory: ``playbook.md`` (lessons distilled before launch from the gate-side records of finished runs; frozen),
  the per-run tables it was distilled from, and ``notes.md``, which the LLM writes itself and finds again next round;
* tools (ls / read / grep) used over several turns before it answers.

Nothing in the workspace or the memory holds an audit score or a test result: ``node_record`` copies named fields
only, and the memory is built by the same function (scripts/meta/build_memory.py).
"""

import copy
import hashlib
import json
import re
import time
from pathlib import Path

from ..core.archive import program_diff
from ..core.types import Program
from .proposers import NumericSearch, _get, _put

NOISE_NOTE = """How to read the evidence.
* A gate is the greedy success rate on unseen scenes ({gate_per_task} per task). Re-scoring one policy on another gate set
  moves the score by about 3 points (one standard deviation); a child against its parent on the same set moves by
  about 3.4 points even when the procedure is unchanged. One gate change under about 6 points is not evidence.
* Evidence that survives the noise: the same direction in several rounds or several runs (run/ledger.tsv,
  memory/prior), a per-task pattern that repeats, or a training-side signal with many tries behind it (sampled
  success over hundreds of tries per inner step; a loss that rises during an update; scenes with both outcomes
  disappearing).
* A change that is kept is not thereby proven: the better of two noisy children is kept about half the time by luck.
"""

HEADER = """You are the meta level of a robot policy that improves itself in simulation: you choose the training procedure of
the next round. Your goal is the success rate of the FINAL policy on unseen scenes after the last round.

Each round, the current policy practises on fresh random scenes of {n_tasks} tasks: curriculum.cases scenes, solver.samples
tries each, sampled at solver.temperature. A simulator marks every try success or failure, and that is the only
feedback. Curation picks the training items: "mixed_groups" (scenes with both outcomes; used with operator "grpo") or
"verified" (successful tries; used with operator "bc"). The update then trains the policy (operator, lr, steps,
batch). A round runs this practise-and-update loop {inner_steps} times, each time with the newest policy.

Each round trains {children} children of the current policy on the same scenes: c0 with the current procedure and the
others with your proposals. All are scored on a new gate set together with the parent; the best child is kept if it
scores at least the parent, and its procedure becomes the current one. This is round {round} of {rounds}.

You work in a workspace of files (index below). Reply with exactly ONE JSON object per turn and nothing else: tools
are called by writing that JSON in your reply; there is no other tool interface and no tag syntax. Either tool calls,
at most {max_calls_per_turn} per turn:
  {{"calls": [{{"tool": "read", "path": "run/nodes/r01c1.json"}}, {{"tool": "grep", "pattern": "bc", "path": "memory/prior"}},
             {{"tool": "ls", "path": "memory/prior"}}]}}
("read" takes optional "start" (first line, from 1) and "lines"; "grep" takes a regular expression and a file or a
folder), or your final answer:
  {{"diagnosis": "<two or three sentences: what limits improvement, and the evidence>",
    "proposals": [{{"why": "<one sentence>", "procedure": <complete procedure JSON>}}, ...],
    "note": "<what you tried this round, what the evidence so far shows, what to try next>"}}
Give {k} DIFFERENT proposals. "note" is appended to memory/notes.md, which you will find again in later rounds.
You have {turns_left} turn(s) left including this one; on your last turn you must give the final answer.

Current procedure (JSON):
{program}

You may change ONLY these fields (numbers are [min, max]; lists are the allowed choices; grpo needs mixed_groups,
bc needs verified). Copy every other field of the procedure unchanged; changes to other fields are discarded:
{space}
{space_doc}

{noise}
Workspace index (path, lines, what it is):
{index}
"""


def node_record(n, parent):
    """Everything the meta level may know about one candidate: named fields only, never audit or test."""
    gain = None if parent is None or n.gate is None or (n.parent_gate is None and parent.gate is None) \
        else round(n.gate - (parent.gate if n.parent_gate is None else n.parent_gate), 4)
    sig = n.signal or {}
    steps = sig.get("inner") or [dict(signal=sig, curation=n.curation, trained=bool(n.receipt))]
    inner = []
    for st in steps:
        cur, s = st.get("curation") or {}, st.get("signal") or {}
        att = cur.get("attempts")
        inner.append(dict(
            step=st.get("step", 0), trained=st.get("trained"),
            sampled_success=None if not att else round(cur.get("verified_attempts", 0) / att, 3),
            mixed_share=None if s.get("mixed_fraction") is None else round(s["mixed_fraction"], 3),
            unsolved_share=None if s.get("unsolved_fraction") is None else round(s["unsolved_fraction"], 3),
            scenes=cur.get("cases"), tries=att, items=cur.get("items"),
            task_sampled_success={str(t): (None if v is None else round(v, 3))
                                  for t, v in (s.get("task_rates") or {}).items()}))
    details = (n.receipt or {}).get("details") or (n.receipt or {}).get("extra") or {}
    try:
        why = json.loads(n.program.note).get("why") if n.program.note.startswith("{") else n.program.note
    except (ValueError, AttributeError):
        why = n.program.note
    return dict(round=n.round, node=n.node_id, parent=n.parent_node, author=n.program.author, why=why,
                changes=program_diff(parent.program.params if parent else {}, n.program.params),
                procedure=n.program.params, gate=n.gate,
                parent_gate=None if parent is None else (parent.gate if n.parent_gate is None else n.parent_gate),
                gate_change=gain, kept=bool(n.accepted),
                gate_tasks=sig.get("gate_tasks"), parent_gate_tasks=sig.get("parent_gate_tasks"),
                inner=inner, loss_first=details.get("loss_first"), loss_last=details.get("loss_last"),
                optimizer_steps=(n.receipt or {}).get("optimizer_steps"))


def records(archive):
    by_id = {n.node_id: n for n in archive.nodes}
    return [node_record(n, by_id.get(n.parent_node)) for n in archive.nodes]


def _f(x, nd=3):
    return "" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def overview_tsv(rows):
    out = ["round\tnode\tauthor\tkept\tgate\tparent_gate\tgate_change\tsampled_success_per_step\tmixed_share_per_step\t"
           "loss_first\tloss_last\tchanges_vs_parent"]
    for r in rows:
        out.append("\t".join([str(r["round"]), r["node"], str(r["author"]), "yes" if r["kept"] else "no",
                              _f(r["gate"]), _f(r["parent_gate"]), _f(r["gate_change"]),
                              "/".join(_f(s["sampled_success"]) for s in r["inner"]),
                              "/".join(_f(s["mixed_share"]) for s in r["inner"]),
                              _f(r["loss_first"], 4), _f(r["loss_last"], 4),
                              json.dumps(r["changes"] if r["round"] else {}, sort_keys=True)]))
    return "\n".join(out) + "\n"


def ledger_tsv(rows):
    """Gate changes pooled per edited field=value over every candidate that carried the edit against its parent."""
    pool = {}
    for r in rows:
        if not r["round"] or r["gate_change"] is None:
            continue
        for knob, value in (r["changes"] or {}).items():
            pool.setdefault(f"{knob}={json.dumps(value)}", []).append((r["gate_change"], r["kept"]))
    out = ["edit\tcandidates\tmean_gate_change\tmin\tmax\tkept"]
    for key, v in sorted(pool.items()):
        d = [x[0] for x in v]
        out.append(f"{key}\t{len(v)}\t{sum(d) / len(d):+.3f}\t{min(d):+.3f}\t{max(d):+.3f}\t{sum(1 for x in v if x[1])}")
    same = [r["gate_change"] for r in rows if r["round"] and r["gate_change"] is not None and not r["changes"]]
    if same:
        out.append(f"(unchanged procedure)\t{len(same)}\t{sum(same) / len(same):+.3f}\t{min(same):+.3f}\t{max(same):+.3f}\t")
    return "\n".join(out) + "\n"


def tasks_tsv(rows):
    """Per task and round: the parent's gate success, each child's gate success, and the last sampled success."""
    tasks = sorted({t for r in rows for t in (r["gate_tasks"] or {})} |
                   {t for r in rows for s in r["inner"] for t in s["task_sampled_success"]}, key=lambda t: int(t))
    out = ["node\twhat\t" + "\t".join(f"task{t}" for t in tasks)]
    for r in rows:
        if r["parent_gate_tasks"] and r["node"].endswith("c0"):
            out.append(f"{r['node']}\tparent_gate\t" + "\t".join(_f(r["parent_gate_tasks"].get(t)) for t in tasks))
        if r["gate_tasks"]:
            out.append(f"{r['node']}\tgate\t" + "\t".join(_f(r["gate_tasks"].get(t)) for t in tasks))
        for s in r["inner"]:
            if s["task_sampled_success"]:
                out.append(f"{r['node']}\tsampled_step{s['step']}\t" +
                           "\t".join(_f(s["task_sampled_success"].get(t)) for t in tasks))
    return "\n".join(out) + "\n"


def run_table(rows):
    """One finished run as a table for memory/prior (the same columns as run/overview.tsv)."""
    return overview_tsv(rows)


class Workspace:
    """Read-only text files addressed by path, with the three tools the LLM may call."""
    MAX_CHARS = 9000

    def __init__(self, files, about=None):
        self.files, self.about = dict(files), dict(about or {})

    def index(self):
        lines = []
        for path in sorted(self.files):
            if path.startswith("memory/prior/") and not path.endswith("INDEX.tsv"):
                continue
            lines.append(f"{path}\t{self.files[path].count(chr(10))}\t{self.about.get(path, '')}")
        n = sum(1 for p in self.files if p.startswith("memory/prior/") and not p.endswith("INDEX.tsv"))
        if n:
            lines.append(f"memory/prior/<run>.tsv\t{n} files\tone table per finished run, same columns as "
                         "run/overview.tsv; the runs are listed in memory/prior/INDEX.tsv")
        return "\n".join(lines)

    def ls(self, path=""):
        path = path.strip("/")
        hits = sorted(p for p in self.files if not path or p == path or p.startswith(path + "/"))
        return "\n".join(f"{p}\t{self.files[p].count(chr(10))} lines" for p in hits) or f"no file under {path}"

    def read(self, path, start=1, lines=None):
        text = self.files.get(path.strip("/"))
        if text is None:
            return f"no such file: {path} (use ls)"
        rows = text.splitlines()
        start = max(1, int(start or 1))
        chunk = rows[start - 1: start - 1 + int(lines)] if lines else rows[start - 1:]
        out = "\n".join(chunk)
        if len(out) > self.MAX_CHARS:
            kept = out[:self.MAX_CHARS].rsplit("\n", 1)[0]
            nxt = start + kept.count("\n") + 1
            out = kept + f"\n[cut: continue with start={nxt}; the file has {len(rows)} lines]"
        return out

    def grep(self, pattern, path=""):
        try:
            rx = re.compile(pattern)
        except re.error as exc:
            return f"bad pattern: {exc}"
        path, out = path.strip("/"), []
        for p in sorted(self.files):
            if path and p != path and not p.startswith(path + "/"):
                continue
            for i, line in enumerate(self.files[p].splitlines(), 1):
                if rx.search(line):
                    out.append(f"{p}:{i}:{line[:400]}")
                    if len(out) >= 80:
                        return "\n".join(out) + "\n[cut at 80 matches: narrow the pattern or the path]"
        return "\n".join(out) or "no match"

    def call(self, c):
        tool = (c or {}).get("tool")
        try:
            if tool == "ls":
                return self.ls(str(c.get("path", "")))
            if tool == "read":
                return self.read(str(c.get("path", "")), c.get("start"), c.get("lines"))
            if tool == "grep":
                return self.grep(str(c.get("pattern", "")), str(c.get("path", "")))
        except (TypeError, ValueError) as exc:
            return f"bad arguments: {exc}"
        return f"unknown tool: {tool} (use ls, read or grep)"


_INVOKE = re.compile(r'<invoke name="(ls|read|grep)">(.*?)</invoke>', re.S)
_PARAM = re.compile(r'<parameter name="(\w+)">(.*?)</parameter>', re.S)


def parse_reply(reply, final_key="proposals", max_calls=4):
    """(data, calls) of one LLM turn. ``data`` is the reply's JSON object ({} if none parses). ``calls`` are its tool
    calls: the "calls" list, or, when the reply used tag syntax instead of JSON (seen in the first distillation run,
    2026-11-10: <invoke name="read"><parameter name="path">...), the distinct calls written that way. A reply that
    holds the final answer has no calls."""
    text, data, decoder = reply or "", {}, json.JSONDecoder()
    for m in re.finditer(r"\{", text):        # the first JSON object that is a turn: a reply may carry stray text or
        try:                                   # a second copy of the object (replay smoke, 2026-11-10)
            obj, _ = decoder.raw_decode(text, m.start())
        except ValueError:
            continue
        if isinstance(obj, dict) and (obj.get(final_key) is not None or obj.get("calls") is not None):
            data = obj
            break
    if data.get(final_key) is not None:
        return data, []
    calls = [c for c in (data.get("calls") or []) if isinstance(c, dict)]
    if not calls:
        for tool, body in _INVOKE.findall(reply or ""):
            c = dict(tool=tool, **{k: v.strip() for k, v in _PARAM.findall(body)})
            if c not in calls:
                calls.append(c)
    return data, calls[:max_calls]


def load_memory(memory_dir):
    """playbook.md and prior/*.tsv of a frozen memory folder as workspace files; {} if the plan names none."""
    files = {}
    if memory_dir:
        root = Path(memory_dir)
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix in (".md", ".tsv"):
                files["memory/" + path.relative_to(root).as_posix()] = path.read_text()
    return files


def memory_digest(memory_dir):
    files = load_memory(memory_dir)
    return hashlib.sha256(json.dumps(sorted(files.items())).encode()).hexdigest()


def build_workspace(archive, program, memory_files, notes):
    rows = records(archive)
    files = {"run/overview.tsv": overview_tsv(rows), "run/ledger.tsv": ledger_tsv(rows),
             "run/tasks.tsv": tasks_tsv(rows),
             "current/procedure.json": json.dumps(program.params, indent=1, sort_keys=True) + "\n",
             "memory/notes.md": notes or "(empty: nothing noted yet in this run)\n"}
    about = {"run/overview.tsv": "every candidate of THIS run, one line each",
             "run/ledger.tsv": "this run's gate changes pooled per edited field=value",
             "run/tasks.tsv": "per task: parent gate, child gate and sampled success per inner step",
             "current/procedure.json": "the current procedure",
             "memory/notes.md": "your own notes from earlier rounds of this run",
             "memory/playbook.md": "lessons distilled from finished runs before this run started; read it first",
             "memory/README.md": "what the memory holds and how its tables are laid out",
             "memory/prior/INDEX.tsv": "the finished runs behind the playbook: suite, start procedure, outcome"}
    for r in rows:
        files[f"run/nodes/{r['node']}.json"] = json.dumps(r, indent=1, sort_keys=True, default=str) + "\n"
        about[f"run/nodes/{r['node']}.json"] = "full record of one candidate"
    files.update(memory_files)
    return Workspace(files, about)


class HarnessMetaProposer:
    """Meta level v3: the LLM works over a workspace and a memory through tool calls, for a few turns per round, then
    proposes k procedures inside the declared edit space. Invalid or failed proposals fall back to ``NumericSearch``.
    Every turn is logged (reply, calls, sizes, usage)."""
    name = "llm_meta_v3"

    def __init__(self, edit_space, validate, fallback: NumericSearch, client, model, out_dir, memory_dir=None,
                 max_calls=60, max_turns=6, temperature=1.0, max_tokens=12000, space_doc="", context=None,
                 max_calls_per_turn=4, transcript_chars=70000):
        self.space, self.validate, self.fallback, self.client = edit_space, validate, fallback, client
        self.model, self.out_dir, self.max_calls, self.max_turns = model, Path(out_dir), max_calls, max_turns
        self.temperature, self.max_tokens, self.space_doc = temperature, max_tokens, space_doc
        self.context = dict(context or {})          # rounds, inner_steps, gate_per_task, n_tasks, children
        self.max_calls_per_turn, self.transcript_chars = max_calls_per_turn, transcript_chars
        self.memory_files = load_memory(memory_dir)
        self.memory_sha256 = memory_digest(memory_dir) if memory_dir else None
        self.calls = 0

    # ------------------------------------------------------------- files in the run dir
    @property
    def notes_path(self):
        return self.out_dir / "meta-notes.md"

    def _notes(self):
        return self.notes_path.read_text() if self.notes_path.exists() else ""

    def _log(self, row):
        with (self.out_dir / "meta-llm.jsonl").open("a") as s:
            s.write(json.dumps(row, default=str) + "\n")

    def _used(self):
        """LLM calls already spent by this run (a resumed run continues the count)."""
        path = self.out_dir / "meta-llm.jsonl"
        if not path.exists():
            return 0
        return sum(len(json.loads(l).get("turns") or []) for l in path.read_text().splitlines() if l.strip())

    # ------------------------------------------------------------------------ one round
    def header(self, program, ws, k, rnd, turns_left):
        return HEADER.format(program=json.dumps(program.params, indent=1, sort_keys=True),
                             space=json.dumps(self.space), space_doc=self.space_doc, k=k, round=rnd,
                             turns_left=turns_left, max_calls_per_turn=self.max_calls_per_turn,
                             noise=NOISE_NOTE.format(gate_per_task=self.context.get("gate_per_task", "?")),
                             index=ws.index(), **{key: self.context.get(key, "?") for key in
                                                  ("rounds", "inner_steps", "n_tasks", "children")})

    def _transcript(self, turns):
        parts = []
        for i, t in enumerate(turns, 1):
            parts.append(f"--- turn {i}, you replied:\n{t['reply']}\n--- turn {i}, tool results:\n{t['results']}")
        text = "\n".join(parts)
        if len(text) > self.transcript_chars:      # keep the newest results whole; shorten the oldest
            text = "[older turns cut]\n" + text[-self.transcript_chars:]
        return text

    def _programs(self, data, program, k, rejected, dropped):
        out = []
        for prop in data.get("proposals") or []:
            try:
                params = self.validate(prop.get("procedure"))
            except (ValueError, TypeError, AttributeError) as exc:
                key = str(exc).split(":")[0] or type(exc).__name__
                rejected[key] = rejected.get(key, 0) + 1
                continue
            outside = sorted(set(program_diff(program.params, params)) - set(self.space))
            if outside:                            # keep the allowed fields of the proposal, drop the rest
                dropped[",".join(outside)] = dropped.get(",".join(outside), 0) + 1
                kept = copy.deepcopy(program.params)
                for knob in self.space:
                    if NumericSearch._has(params, knob):
                        _put(kept, knob, _get(params, knob))
                try:
                    params = self.validate(kept)
                except (ValueError, TypeError) as exc:
                    key = str(exc).split(":")[0] or type(exc).__name__
                    rejected[key] = rejected.get(key, 0) + 1
                    continue
            if params != program.params and all(params != p.params for p in out):
                note = json.dumps(dict(why=str(prop.get("why", ""))[:300], diff=program_diff(program.params, params)))
                out.append(Program.make(params, program.id, "llm", note))
            if len(out) >= k:
                break
        return out

    def propose(self, program, archive, backend, version, k, rng):
        rnd = max([n.round for n in archive.nodes] or [0]) + 1
        ws = build_workspace(archive, program, self.memory_files, self._notes())
        turns, out, rejected, dropped, diagnosis, note, usage_sum = [], [], {}, {}, None, None, {}
        self.calls = self._used()
        for turn in range(1, self.max_turns + 1):
            if self.calls >= self.max_calls:
                rejected["call_cap"] = self.max_calls
                break
            last = turn == self.max_turns
            prompt = self.header(program, ws, k, rnd, self.max_turns - turn + 1)
            if turns:
                prompt += "\nTranscript of this round so far:\n" + self._transcript(turns)
            prompt += "\n\nYour last turn: give the final answer now. JSON only:" if last else "\n\nJSON only:"
            self.calls += 1
            t0 = time.time()
            try:
                reply, usage = self.client(prompt, self.temperature, self.max_tokens)
            except RuntimeError as exc:
                rejected["call"] = str(exc)[:120]
                turns.append(dict(reply=None, results="", calls=[], prompt_chars=len(prompt),
                                  seconds=round(time.time() - t0)))
                break
            secs = round(time.time() - t0)
            for key, v in (usage or {}).items():
                if isinstance(v, (int, float)):
                    usage_sum[key] = usage_sum.get(key, 0) + v
            data, calls = parse_reply(reply, "proposals", self.max_calls_per_turn)
            if data.get("proposals") is not None:
                diagnosis, note = str(data.get("diagnosis", ""))[:800], str(data.get("note", "") or "")[:2000]
                out = self._programs(data, program, k, rejected, dropped)
                turns.append(dict(reply=reply, results="", calls=[], prompt_chars=len(prompt), final=True,
                                  seconds=secs))
                break
            if not calls:
                results = ('Your reply was not a JSON object with "calls" or "proposals". Reply with one JSON '
                           'object only.')
                rejected["unparsed_turn"] = rejected.get("unparsed_turn", 0) + 1
            else:
                results = "\n".join(f"[{json.dumps(c, sort_keys=True)}]\n{ws.call(c)}" for c in calls)
            turns.append(dict(reply=reply, results=results, calls=calls, prompt_chars=len(prompt), seconds=secs))
        if note:
            with self.notes_path.open("a") as s:
                s.write(f"## round {rnd}\n{note}\n\n")
        n_llm = len(out)
        if len(out) < k:
            out += self.fallback.propose(program, archive, backend, version, k - len(out), rng)
        self._log(dict(model=self.model, round=rnd, memory_sha256=self.memory_sha256, diagnosis=diagnosis, note=note,
                       turns=[dict(reply=t["reply"], calls=t["calls"], result_chars=len(t["results"]),
                                   prompt_chars=t["prompt_chars"], final=t.get("final", False),
                                   seconds=t.get("seconds")) for t in turns],
                       usage=usage_sum, llm_programs=n_llm, fallback_programs=len(out) - n_llm,
                       rejected=rejected, dropped_fields=dropped,
                       workspace={p: hashlib.sha256(t.encode()).hexdigest()[:16] for p, t in ws.files.items()
                                  if not p.startswith("memory/prior/")}))
        return out[:k]
