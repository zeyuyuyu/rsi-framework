"""Smoke test of meta level v3 without a GPU: replay the first <rounds> rounds of a finished run's archive and ask the
harness proposer for the next round's procedures (a real LLM call sequence). Nothing is trained; the output directory
receives meta-llm.jsonl and meta-notes.md exactly as a run would.

usage: replay_smoke.py <run dir with archive.jsonl> <rounds kept, 0 = only n0> <suite> <out dir> <base_url> <model> <key_file>
"""
import json
import random
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_memory import load                           # noqa: E402
from rsi.core.archive import Archive                    # noqa: E402
from rsi.domains.libero.domain import LiberoDomain      # noqa: E402
from rsi.meta.harness import HarnessMetaProposer        # noqa: E402
from rsi.meta.proposers import NumericSearch, OpenAICompatClient   # noqa: E402

run, rounds, suite, out = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
nodes = [n for n in load(run) if n.round <= rounds]
for n in nodes:
    n.audit = None
archive = Archive(Path(tempfile.mkdtemp()) / "a.jsonl")
for n in nodes:
    archive.add(n)
parent = [n for n in nodes if n.accepted][-1]
d = LiberoDomain(suite, range(10), v2=True)
doc = d.v2_doc + "\n" + d.set_budget_cap(nodes[0].program.params)
out.mkdir(parents=True, exist_ok=True)
prop = HarnessMetaProposer(d.v2_space, d.validate_capped, NumericSearch(d.harness_space, d.validate_capped, d.coupling),
                           OpenAICompatClient(sys.argv[5], sys.argv[6], sys.argv[7], timeout=300), sys.argv[6], out,
                           memory_dir=REPO / "rsi" / "meta" / "memory" / "v3", space_doc=doc,
                           context=dict(rounds=6, inner_steps=3, gate_per_task=20, n_tasks=10, children=2))
progs = prop.propose(parent.program, archive, None, None, 1, random.Random(0))
row = json.loads((out / "meta-llm.jsonl").read_text().splitlines()[-1])
print("turns", len(row["turns"]), "usage", row["usage"], "rejected", row["rejected"], "dropped", row["dropped_fields"])
for t in row["turns"]:
    print("  calls", json.dumps(t["calls"])[:300], "| prompt chars", t["prompt_chars"])
print("diagnosis:", row["diagnosis"])
print("note:", row["note"])
for p in progs:
    print("proposal by", p.author, p.note)
