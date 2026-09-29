"""Subject programs.

Each subject is a specification circuit plus the observed qubits on which its
contract is stated.  *State* contracts constrain the prepared output state;
*process* contracts constrain a subroutine through its Choi state, i.e. the
program is applied to one half of maximally entangled reference pairs whose
preparation is marked ideal (the ancilla-free protocol replaces it by
randomised stabilizer inputs; see Section IV-D).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .circuits import Circuit


@dataclass
class Subject:
    name: str
    family: str          # e.g. "entangled state", "QEC encoder", "channel"
    contract: str        # "state" or "process"
    spec: Circuit
    observed: list
    description: str

    @property
    def n(self) -> int:
        return self.spec.n


def _ghz(n: int) -> Circuit:
    c = Circuit(n, name=f"GHZ-{n}")
    c.add("h", 0)
    for i in range(n - 1):
        c.add("cx", i, i + 1)
    return c


def _swap_as_cx(c: Circuit, a: int, b: int) -> None:
    c.add("cx", a, b).add("cx", b, a).add("cx", a, b)


def bell() -> Subject:
    c = Circuit(2, name="Bell").add("h", 0).add("cx", 0, 1)
    return Subject("Bell", "entangled state", "state", c, [0, 1], "Bell pair |Phi+>")


def ghz(n: int) -> Subject:
    return Subject(f"GHZ-{n}", "entangled state", "state", _ghz(n), list(range(n)),
                   f"{n}-qubit GHZ state (CNOT chain)")


def cluster(n: int) -> Subject:
    c = Circuit(n, name=f"Cluster-{n}")
    for q in range(n):
        c.add("h", q)
    for q in range(n - 1):
        c.add("cz", q, q + 1)
    return Subject(f"Cluster-{n}", "graph state", "state", c, list(range(n)),
                   f"{n}-qubit linear cluster state")


def ring(n: int) -> Subject:
    c = Circuit(n, name=f"Ring-{n}")
    for q in range(n):
        c.add("h", q)
    for q in range(n):
        c.add("cz", q, (q + 1) % n)
    return Subject(f"Ring-{n}", "graph state", "state", c, list(range(n)),
                   f"{n}-qubit ring graph state (odd ring: three settings)")


def steane_zero() -> Subject:
    """Steane [[7,1,3]] logical |0>: uniform superposition over the row space
    of the Hamming parity-check matrix, prepared by three fan-outs."""
    rows = {3: [4, 5, 6], 1: [2, 5, 6], 0: [2, 4, 6]}
    c = Circuit(7, name="Steane-0L")
    for piv in rows:
        c.add("h", piv)
    for piv, targets in rows.items():
        for t in targets:
            c.add("cx", piv, t)
    return Subject("Steane-7", "QEC encoder", "state", c, list(range(7)),
                   "Steane code logical |0_L> encoder")


def qft(n: int, x: int) -> Subject:
    c = Circuit(n, name=f"QFT-{n}")
    for q in range(n):
        if (x >> (n - 1 - q)) & 1:
            c.add("x", q)
    for j in range(n):
        c.add("h", j)
        for k in range(j + 1, n):
            c.add("cp", k, j, params=[np.pi / 2 ** (k - j)])
    for q in range(n // 2):
        _swap_as_cx(c, q, n - 1 - q)
    return Subject(f"QFT-{n}", "arithmetic (non-Clifford)", "state", c, list(range(n)),
                   f"QFT of basis input |{x}> (product target, controlled phases)")


def bernstein_vazirani(secret: str) -> Subject:
    n = len(secret)
    c = Circuit(n + 1, name="BV")
    c.add("x", n).add("h", n)
    for q in range(n):
        c.add("h", q)
    for q, bit in enumerate(secret):
        if bit == "1":
            c.add("cx", q, n)
    for q in range(n):
        c.add("h", q)
    return Subject(f"BV-{n}", "oracle algorithm", "state", c, list(range(n)),
                   f"Bernstein-Vazirani, secret {secret} (basis-state target)")


def _choi(n_in: int, n_extra: int, body: Callable[[Circuit, list, list], None], name: str) -> Circuit:
    """Reference qubits 0..n_in-1, program inputs n_in..2n_in-1, extras after."""
    c = Circuit(2 * n_in + n_extra, name=name)
    refs = list(range(n_in))
    ins = list(range(n_in, 2 * n_in))
    extra = list(range(2 * n_in, 2 * n_in + n_extra))
    for r, i in zip(refs, ins):
        c.add("h", r, ideal=True)
        c.add("cx", r, i, ideal=True)
    body(c, ins, extra)
    return c


def teleportation() -> Subject:
    def body(c, ins, extra):
        q0, (q1, q2) = ins[0], extra
        c.add("h", q1).add("cx", q1, q2)      # resource Bell pair
        c.add("cx", q0, q1).add("h", q0)      # Bell-basis rotation
        c.add("cx", q1, q2).add("cz", q0, q2)  # deferred corrections
    c = _choi(1, 2, body, "Teleport")
    return Subject("Teleport", "channel", "process", c, [0, 3],
                   "Teleportation channel q0 -> q2 (deferred measurement)")


def swap_channel() -> Subject:
    def body(c, ins, extra):
        _swap_as_cx(c, ins[0], ins[1])
    c = _choi(2, 0, body, "SWAP")
    return Subject("SWAP-3CX", "channel", "process", c, [0, 1, 2, 3],
                   "Two-qubit SWAP compiled to three CNOTs")


def repetition_encoder() -> Subject:
    def body(c, ins, extra):
        c.add("cx", ins[0], extra[0]).add("cx", ins[0], extra[1])
    c = _choi(1, 2, body, "Rep3")
    return Subject("Rep3-Enc", "QEC encoder", "process", c, [0, 1, 2, 3],
                   "Three-qubit repetition-code encoder (isometry)")


def default_suite() -> list[Subject]:
    return [
        bell(), ghz(4), ghz(8), cluster(6), ring(5), steane_zero(),
        bernstein_vazirani("10110"), qft(4, 0b1011),
        teleportation(), swap_channel(), repetition_encoder(),
    ]
