"""Build the frozen memory of meta level v3 (addendum 29) from finished runs' gate-side records.

For every listed run with an archive.jsonl (the A800 runs; Yangquan records keep no procedure per candidate), write
memory/<name>/prior/<run>.tsv with the columns of the live workspace's run/overview.tsv, and prior/INDEX.tsv with one
line per run. The tables come from rsi.meta.harness.node_record, which copies named fields only: no audit score and
no test result can enter. Runs of control arms the meta level cannot choose (nonrec, shuffled, onebig), replicate
evaluations, voided runs and the running addendum-28 runs are left out.

usage: build_memory.py <memory name> [results root=results/a800]      -> rsi/meta/memory/<name>/prior/
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from rsi.core.archive import Node                      # noqa: E402
from rsi.core.types import Program, Version            # noqa: E402
from rsi.meta.harness import node_record, overview_tsv  # noqa: E402

INCLUDE = re.compile(r"^a8_(goalmain_(fixed|llm|llm_harness_cap)_s\d|m2_(pre|tun)_(llm|rep)_s\d|"
                     r"oftgb_(fixed|full|llm_harness)_s\d|oftg_curve_(bc|bct|grpo)_s\d|ofts_curve_grpo_s\d|"
                     r"spatmain_llm_harness_cap_s\d|pilot_fail\d_s\d|oft3_pilot\d\w*_s\d)$")
EXCLUDE = {"a8_spatmain_fixed_s0", "a8_spatmain_nonrec_s0", "a8_spatmain_shuffled_s0", "a8_spatmain_onebig_s0"}


README = """Memory of the meta level: records of finished runs of the same self-improvement loop.

prior/INDEX.tsv  one line per finished run: suite, who proposed procedures (fixed = nobody, replica = two copies of
                 the same procedure, numeric = blind search, llm = an earlier LLM meta level), the procedure the run
                 started from, rounds, candidates trained, candidates kept, the sum of the gate changes of the kept
                 candidates, the lowest gate of the run, and how the last kept procedure differs from the start.
prior/<run>.tsv  one line per candidate. gate: greedy success on that round's unseen gate scenes. parent_gate: the
                 parent policy on the same scenes. gate_change: gate - parent_gate. sampled_success_per_step: success
                 rate of the practice tries in each inner step (hundreds of tries each). mixed_share_per_step: share
                 of practice scenes with both outcomes. loss_first / loss_last: training loss at the first and last
                 step of the last update. changes_vs_parent: fields that differ from the parent's procedure.
Runs whose proposer is fixed and that kept every round are always-accept curves (no gate decision).
A kept candidate was the best child of its round and scored at least its parent; with gate noise of about 3 points
that happens by luck about half the time, so sum_gate_change_of_kept overstates the real gain of a run.
Nothing here holds a test result.
"""


def load(run):
    nodes, events = {}, []
    for line in (run / "archive.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("event") == "accepted":
            events.append(row)
        else:
            nodes[row["node_id"]] = Node(**dict(row, version=Version(**row["version"]),
                                                program=Program(**row["program"])))
    for e in events:
        if e["node_id"] in nodes:
            nodes[e["node_id"]].accepted = True
    return list(nodes.values())


def start_of(params):
    u, c, s, cu = params["update"], params["curation"], params["solver"], params["curriculum"]
    extra = ",".join(f"{k}={u[k]}" for k in ("ratio", "loss_agg", "bc_temp") if k in u)
    return (f"{u['operator']} lr={u['lr']:g} steps={u['steps']}x{u['batch']} T={s['temperature']} "
            f"scenes={cu['cases']}x{s['samples']} {extra}").strip()


def main():
    name = sys.argv[1]
    root = REPO / (sys.argv[2] if len(sys.argv) > 2 else "results/a800")
    out = REPO / "rsi" / "meta" / "memory" / name / "prior"
    out.mkdir(parents=True, exist_ok=True)
    index = ["run\tsuite\tproposer\tstart_procedure\trounds\tcandidates\tkept\tsum_gate_change_of_kept\t"
             "lowest_gate\tfinal_procedure_vs_start"]
    for run in sorted((root / "runs2").iterdir()):
        if not INCLUDE.match(run.name) or run.name in EXCLUDE or not (run / "archive.jsonl").exists():
            continue
        nodes = load(run)
        by_id = {n.node_id: n for n in nodes}
        rows = [node_record(n, by_id.get(n.parent_node)) for n in nodes]
        if len(rows) < 2:
            continue
        (out / f"{run.name}.tsv").write_text(overview_tsv(rows))
        plan_path = root / "plans2" / f"{run.name}.json"
        plan = json.loads(plan_path.read_text()) if plan_path.exists() else {}
        kept = [r for r in rows if r["round"] and r["kept"]]
        gates = [r["gate"] for r in rows if r["gate"] is not None]
        from rsi.core.archive import program_diff
        last = kept[-1]["procedure"] if kept else rows[0]["procedure"]
        index.append("\t".join([
            run.name, plan.get("suite", "?"), (plan.get("meta") or {}).get("proposer", "?") +
            ("+" + plan["meta"]["space"] if (plan.get("meta") or {}).get("space") else ""),
            start_of(rows[0]["procedure"]), str(max(r["round"] for r in rows)), str(len(rows) - 1), str(len(kept)),
            f"{sum(r['gate_change'] or 0 for r in kept):+.3f}", f"{min(gates):.3f}",
            json.dumps(program_diff(rows[0]["procedure"], last), sort_keys=True)]))
    (out / "INDEX.tsv").write_text("\n".join(index) + "\n")
    (out.parent / "README.md").write_text(README)
    print(len(index) - 1, "runs ->", out)


if __name__ == "__main__":
    main()
