"""Value types shared by the engine, domains, backends and meta-level proposers.

Two things are versioned and inherited across rounds:
  * ``Version`` - the model state (weights / adapter) being improved;
  * ``Program`` - the improvement program that turns the model's own
    experience into the next version (curriculum, solver, curation, update).
Improving the second is what makes the loop recursive beyond a training run.
"""

from dataclasses import dataclass, field
import hashlib
import json
from typing import Protocol, Sequence


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class Version:
    id: str
    location: str
    parent_id: str | None = None


@dataclass(frozen=True)
class Program:
    id: str
    params: dict
    parent_id: str | None = None
    author: str = "seed"          # seed | self | search | agent
    note: str = ""

    @staticmethod
    def make(params, parent_id=None, author="seed", note=""):
        return Program(digest(params)[:16], params, parent_id, author, note)


@dataclass(frozen=True)
class Case:
    """One task instance. ``label`` is never shown to the model."""
    id: str
    group: str
    split: str                     # train | gate | audit | test
    inputs: object
    oracle: str                    # provenance of the external judgement
    label: object = None


@dataclass(frozen=True)
class Attempt:
    case_id: str
    reward: float                  # external verifier's native reward
    verified: bool                 # external verifier accepted the attempt
    experience: object             # what an update operator may train on
    details: object = None


@dataclass(frozen=True)
class EvalRecord:
    id: str
    score: float
    prediction: object = None
    details: object = None


@dataclass(frozen=True)
class Receipt:
    version: Version
    operator: str
    optimizer_steps: int
    items: int
    trainable_parameters: int
    before_sha256: str
    after_sha256: str
    details: dict = field(default_factory=dict)


class Domain(Protocol):
    """Everything task-specific: case generation, acting, the oracle, metrics."""

    name: str
    higher_is_better: bool

    def default_program(self) -> dict: ...

    def validate_program(self, params: dict) -> dict: ...

    def propose(self, backend, generator: Version, program: dict, round_index: int,
                seed: int) -> list[Case]: ...

    def attempt(self, backend, generator: Version, cases: Sequence[Case], program: dict,
                seed: int) -> list[list[Attempt]]: ...

    def evaluate(self, backend, version: Version, cases: Sequence[Case]) -> list[EvalRecord]: ...

    def leakage_key(self, case: Case) -> str: ...

    def signal_metrics(self, cases: Sequence[Case],
                       attempts: Sequence[Sequence[Attempt]]) -> dict: ...


class Backend(Protocol):
    """Model-specific acting and real parameter updates."""

    def train(self, parent: Version, items: Sequence[object], output, update: dict,
              seed: int) -> Receipt: ...
