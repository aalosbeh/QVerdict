"""A minimal, explicit gate-list circuit representation.

A gate is a tuple ``(name, qubits, params)``.  Gates flagged as *ideal* are
never subject to noise or mutation; they model the reference half of a Choi
(ancilla-assisted) construction, which the ancilla-free protocol replaces by
randomised input-state preparation (Section IV-D of the paper).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

ONE_QUBIT = ("h", "x", "y", "z", "s", "sdg", "t", "tdg", "id", "rx", "ry", "rz", "p")
TWO_QUBIT = ("cx", "cz", "swap", "cp")
INVERSE = {"h": "h", "x": "x", "y": "y", "z": "z", "s": "sdg", "sdg": "s", "t": "tdg",
           "tdg": "t", "id": "id", "cx": "cx", "cz": "cz", "swap": "swap"}
PARAMETRIC = ("rx", "ry", "rz", "p", "cp")

Gate = tuple  # (name: str, qubits: tuple[int, ...], params: tuple[float, ...])


def gate(name: str, *qubits: int, params: Sequence[float] = ()) -> Gate:
    name = name.lower()
    if name not in ONE_QUBIT + TWO_QUBIT:
        raise ValueError(f"unknown gate {name!r}")
    arity = 1 if name in ONE_QUBIT else 2
    if len(qubits) != arity:
        raise ValueError(f"gate {name} expects {arity} qubit(s)")
    if len(set(qubits)) != len(qubits):
        raise ValueError("repeated qubit in gate")
    return (name, tuple(int(q) for q in qubits), tuple(float(p) for p in params))


def inverse_gate(g: Gate) -> Gate:
    name, qubits, params = g
    if name in PARAMETRIC:
        return (name, qubits, tuple(-p for p in params))
    return (INVERSE[name], qubits, params)


@dataclass
class Circuit:
    """An ``n``-qubit circuit with optional ideal (noise- and mutation-free) gates."""

    n: int
    gates: list = field(default_factory=list)
    ideal: set = field(default_factory=set)  # indices of ideal gates
    name: str = ""

    def add(self, name: str, *qubits: int, params: Sequence[float] = (), ideal: bool = False) -> "Circuit":
        g = gate(name, *qubits, params=params)
        if max(g[1]) >= self.n:
            raise ValueError("qubit index out of range")
        if ideal:
            self.ideal.add(len(self.gates))
        self.gates.append(g)
        return self

    def copy(self) -> "Circuit":
        return Circuit(self.n, list(self.gates), set(self.ideal), self.name)

    def mutable_indices(self) -> list[int]:
        return [i for i in range(len(self.gates)) if i not in self.ideal]

    def inverse(self) -> "Circuit":
        m = len(self.gates)
        inv = Circuit(self.n, [inverse_gate(g) for g in reversed(self.gates)], name=self.name + "^-1")
        inv.ideal = {m - 1 - i for i in self.ideal}
        return inv

    def compose(self, other: "Circuit") -> "Circuit":
        if other.n != self.n:
            raise ValueError("width mismatch")
        out = self.copy()
        off = len(out.gates)
        out.gates.extend(other.gates)
        out.ideal |= {off + i for i in other.ideal}
        return out

    def is_clifford(self) -> bool:
        from .pauli import CLIFFORD_GATES

        return all(g[0] in CLIFFORD_GATES for g in self.gates)

    def two_qubit_count(self, include_ideal: bool = False) -> int:
        return sum(1 for i, g in enumerate(self.gates)
                   if len(g[1]) == 2 and (include_ideal or i not in self.ideal))

    def depth(self) -> int:
        level = np.zeros(self.n, dtype=int)
        for name, qubits, _ in self.gates:
            d = max(level[list(qubits)]) + 1
            level[list(qubits)] = d
        return int(level.max(initial=0))

    def __len__(self) -> int:
        return len(self.gates)
