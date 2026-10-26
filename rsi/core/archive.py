"""Append-only archive of every (version, program) the loop produced.

Each node records the model version, the improvement program that produced
it, its parent node, gate/audit scores, signal metrics of the experience it
was trained on, compute, and whether it was accepted. Meta-level proposers
read summaries of the archive; nothing in it is ever overwritten.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path

from .types import Program, Version


@dataclass
class Node:
    node_id: str
    round: int
    version: Version
    program: Program
    parent_node: str | None
    gate: float | None = None
    audit: float | None = None
    accepted: bool = False
    signal: dict = field(default_factory=dict)
    curation: dict = field(default_factory=dict)
    receipt: dict = field(default_factory=dict)
    seconds: dict = field(default_factory=dict)


class Archive:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.nodes: list[Node] = []

    def add(self, node: Node) -> Node:
        self.nodes.append(node)
        with self.path.open("a") as stream:
            stream.write(json.dumps(asdict(node), sort_keys=True, default=str) + "\n")
        return node

    def mark_accepted(self, node: Node) -> None:
        """Acceptance is decided after the node is recorded; append it as an event."""
        node.accepted = True
        with self.path.open("a") as stream:
            stream.write(json.dumps(dict(event="accepted", node_id=node.node_id,
                                         audit=node.audit, gate=node.gate)) + "\n")

    def get(self, node_id):
        return next(n for n in self.nodes if n.node_id == node_id)

    def accepted(self):
        return [n for n in self.nodes if n.accepted]

    def best(self, higher_is_better=True):
        pool = self.accepted()
        sign = 1 if higher_is_better else -1
        return max(pool, key=lambda n: (sign * n.gate, n.round)) if pool else None

    def children(self, node_id):
        return [n for n in self.nodes if n.parent_node == node_id]

    def summary(self, limit=24):
        """Compact history for proposers: program changes and the gate change they caused."""
        rows = []
        for n in self.nodes[-limit:]:
            parent = self.get(n.parent_node) if n.parent_node else None
            gain = None if parent is None or n.gate is None or parent.gate is None \
                else n.gate - parent.gate
            changes = program_diff(parent.program.params if parent else {}, n.program.params)
            rows.append(dict(round=n.round, node=n.node_id, author=n.program.author,
                             changes=changes, gate=n.gate, gate_gain=gain,
                             accepted=n.accepted,
                             verified_rate=n.signal.get("verified_rate"),
                             cases=n.signal.get("cases")))
        return rows


def program_diff(old: dict, new: dict, prefix=""):
    out = {}
    for key in sorted(set(old) | set(new)):
        a, b = old.get(key), new.get(key)
        name = f"{prefix}{key}"
        if isinstance(a, dict) and isinstance(b, dict):
            out.update(program_diff(a, b, name + "."))
        elif a != b:
            out[name] = b if not isinstance(b, str) or len(b) < 80 else b[:77] + "..."
    return out
