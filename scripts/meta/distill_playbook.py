"""Distil memory/<name>/playbook.md from the prior-run tables (addendum 29), with the LLM and the tools of the v3
harness. Run once before launch, on a machine that holds the gateway key; the log of every turn is kept next to the
playbook. The playbook is then frozen: its digest is written into every plan (meta.memory_sha256).

usage: distill_playbook.py <memory dir> <base_url> <model> <key_file> [max_turns=14]

The first attempt (2026-11-10 05:20Z, kept as distill-log-attempt1.jsonl) wrote no playbook: the reply cap of 6000
tokens was used up by the model's reasoning on the last turns, and some turns used tag syntax for tool calls, which
the parser did not read. This version allows 16000 tokens and reads both syntaxes.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rsi.meta.harness import Workspace, load_memory, parse_reply    # noqa: E402
from rsi.meta.proposers import OpenAICompatClient      # noqa: E402

PROMPT = """You are preparing the memory of the meta level of a robot policy that improves itself in simulation.

The loop: each round, the current policy practises on fresh random scenes of 10 manipulation tasks (curriculum.cases
scenes, solver.samples tries each, sampled at solver.temperature); a simulator marks every try success or failure.
Curation picks training items ("mixed_groups": scenes with both outcomes, used with operator "grpo"; "verified":
successful tries, used with operator "bc"); the update trains the policy (operator, lr, steps, batch). A round runs
this practise-and-update loop three times. Children of the current policy are scored on a new gate set (greedy
success on unseen scenes, 20 per task) together with the parent; the best child is kept if it scores at least the
parent. A meta level may change the procedure between rounds.

The records of finished runs are files (index below; start with memory/README.md and memory/prior/INDEX.tsv).
Read them, then write a playbook that the meta level will read at the start of every round of future runs, which
may be on another task suite and may start from another procedure. Requirements:
* every lesson names the runs and the numbers behind it;
* say what the records support and what they do not; where an edit was tried several times without a consistent
  effect, say so (negative evidence is as useful as positive);
* describe the training-side signatures that came before a policy got worse, and what brought it back;
* estimate from the records how much the gate moves between identical procedures, and say what size of change
  counts as evidence;
* say which procedures were reliable starting points and which were not;
* at most 70 lines of plain markdown, no preamble.

Reply with exactly ONE JSON object per turn and nothing else: tools are called by writing that JSON in your reply;
there is no other tool interface and no tag syntax. Either tool calls, at most 4 per turn:
  {{"calls": [{{"tool": "read", "path": "memory/prior/INDEX.tsv"}}, {{"tool": "grep", "pattern": "bc", "path": "memory/prior"}}]}}
("read" takes optional "start" and "lines"; "grep" takes a regular expression and a file or folder; "ls" lists),
or the final answer:  {{"playbook": "<markdown>"}}
You have {turns_left} turn(s) left including this one; on your last turn you must give the final answer.

Files (path, lines):
{index}
"""


def main():
    mem = Path(sys.argv[1])
    client = OpenAICompatClient(sys.argv[2], sys.argv[3], sys.argv[4], timeout=600)
    max_turns = int(sys.argv[5]) if len(sys.argv) > 5 else 14
    files = {p: t for p, t in load_memory(mem).items() if p != "memory/playbook.md"}
    ws = Workspace(files)
    index = "\n".join(f"{p}\t{t.count(chr(10))}" for p, t in sorted(files.items()))
    turns, log = [], mem / "distill-log.jsonl"
    for turn in range(1, max_turns + 1):
        prompt = PROMPT.format(turns_left=max_turns - turn + 1, index=index)
        if turns:
            text = "\n".join(f"--- turn {i}, you replied:\n{t['reply']}\n--- turn {i}, tool results:\n{t['results']}"
                             for i, t in enumerate(turns, 1))
            prompt += "\nTranscript so far:\n" + text[-150000:]
        prompt += "\n\nYour last turn: give the final answer now. JSON only:" if turn == max_turns else "\n\nJSON only:"
        reply, usage = client(prompt, 1.0, 16000)     # the gateway counts reasoning inside max_tokens
        data, calls = parse_reply(reply, "playbook", 4)
        results = "\n".join(f"[{json.dumps(c, sort_keys=True)}]\n{ws.call(c)}" for c in calls) if calls else \
            "Reply with one JSON object holding \"calls\" or \"playbook\"."
        with log.open("a") as s:
            s.write(json.dumps(dict(turn=turn, model=sys.argv[3], reply=reply, calls=calls, usage=usage,
                                    prompt_chars=len(prompt), result_chars=len(results))) + "\n")
        if isinstance(data, dict) and data.get("playbook"):
            (mem / "playbook.md").write_text(str(data["playbook"]).strip() + "\n")
            print("playbook written after", turn, "turns;", len(str(data["playbook"]).splitlines()), "lines")
            return
        turns.append(dict(reply=reply, results=results))
    raise SystemExit("no playbook after the last turn")


if __name__ == "__main__":
    main()
