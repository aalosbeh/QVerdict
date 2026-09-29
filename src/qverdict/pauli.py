"""Pauli strings, Clifford conjugation and stabilizer groups.

Conventions
-----------
* A Pauli string on ``n`` qubits is stored as ``(phase, ops)`` where ``ops`` is a
  string over ``"IXYZ"`` and ``ops[q]`` acts on qubit ``q``.  Qubit 0 is the
  *first* tensor factor (big-endian), matching :mod:`qverdict.simulator`.
* ``phase`` is one of ``1, -1, 1j, -1j``.  Elements of a stabilizer group are
  Hermitian, so their phase is ``+1`` or ``-1``.

The routines are exact and intended for the small registers (n <= 12) used in
test oracles; they favour clarity over asymptotic speed.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from typing import Iterable, Sequence

import numpy as np

# Single-qubit products a*b = phase * c.
_MUL = {
    ("I", "I"): (1, "I"), ("I", "X"): (1, "X"), ("I", "Y"): (1, "Y"), ("I", "Z"): (1, "Z"),
    ("X", "I"): (1, "X"), ("X", "X"): (1, "I"), ("X", "Y"): (1j, "Z"), ("X", "Z"): (-1j, "Y"),
    ("Y", "I"): (1, "Y"), ("Y", "X"): (-1j, "Z"), ("Y", "Y"): (1, "I"), ("Y", "Z"): (1j, "X"),
    ("Z", "I"): (1, "Z"), ("Z", "X"): (1j, "Y"), ("Z", "Y"): (-1j, "X"), ("Z", "Z"): (1, "I"),
}

_MATS = {
    "I": np.eye(2, dtype=complex),
    "X": np.array([[0, 1], [1, 0]], dtype=complex),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "Z": np.array([[1, 0], [0, -1]], dtype=complex),
}


def _clean_phase(p: complex) -> complex:
    for c in (1, -1, 1j, -1j):
        if abs(p - c) < 1e-9:
            return c
    raise ValueError(f"invalid Pauli phase {p}")


@dataclass(frozen=True)
class Pauli:
    """An n-qubit Pauli operator ``phase * ops[0] (x) ops[1] (x) ...``."""

    phase: complex
    ops: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "phase", _clean_phase(self.phase))
        if any(c not in "IXYZ" for c in self.ops):
            raise ValueError(f"invalid Pauli letters in {self.ops!r}")

    # ------------------------------------------------------------------ basics
    @property
    def n(self) -> int:
        return len(self.ops)

    @staticmethod
    def identity(n: int) -> "Pauli":
        return Pauli(1, "I" * n)

    @staticmethod
    def single(n: int, q: int, letter: str, phase: complex = 1) -> "Pauli":
        ops = ["I"] * n
        ops[q] = letter
        return Pauli(phase, "".join(ops))

    @staticmethod
    def from_label(label: str) -> "Pauli":
        """Parse labels such as ``"XZ"``, ``"-YY"`` or ``"+IZX"``."""
        phase = 1
        if label.startswith("-"):
            phase, label = -1, label[1:]
        elif label.startswith("+"):
            label = label[1:]
        return Pauli(phase, label)

    def __mul__(self, other: "Pauli") -> "Pauli":
        if self.n != other.n:
            raise ValueError("Pauli length mismatch")
        phase = self.phase * other.phase
        out = []
        for a, b in zip(self.ops, other.ops):
            p, c = _MUL[(a, b)]
            phase *= p
            out.append(c)
        return Pauli(phase, "".join(out))

    def __neg__(self) -> "Pauli":
        return Pauli(-self.phase, self.ops)

    def commutes(self, other: "Pauli") -> bool:
        anti = sum(1 for a, b in zip(self.ops, other.ops) if a != "I" and b != "I" and a != b)
        return anti % 2 == 0

    def weight(self) -> int:
        return sum(c != "I" for c in self.ops)

    def support(self) -> tuple[int, ...]:
        return tuple(q for q, c in enumerate(self.ops) if c != "I")

    def is_hermitian(self) -> bool:
        return self.phase in (1, -1)

    def sign(self) -> int:
        if not self.is_hermitian():
            raise ValueError("non-Hermitian Pauli has no sign")
        return int(self.phase.real) if isinstance(self.phase, complex) else int(self.phase)

    def matrix(self) -> np.ndarray:
        return self.phase * reduce(np.kron, (_MATS[c] for c in self.ops))

    def label(self) -> str:
        s = {1: "+", -1: "-", 1j: "+i", -1j: "-i"}[self.phase]
        return s + self.ops

    def restrict(self, qubits: Sequence[int]) -> "Pauli":
        return Pauli(self.phase, "".join(self.ops[q] for q in qubits))

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"Pauli({self.label()})"


# ---------------------------------------------------------------- Cliffords
def _images(name: str, qubits: Sequence[int], n: int) -> dict[tuple[str, int], Pauli]:
    """Images U X_q U^dagger and U Z_q U^dagger for the qubits a gate touches."""
    P = lambda q, l, s=1: Pauli.single(n, q, l, s)  # noqa: E731
    if name in ("h", "s", "sdg", "x", "y", "z", "id"):
        (q,) = qubits
        table = {
            "h": (P(q, "Z"), P(q, "X")),
            "s": (P(q, "Y"), P(q, "Z")),
            "sdg": (P(q, "Y", -1), P(q, "Z")),
            "x": (P(q, "X"), P(q, "Z", -1)),
            "y": (P(q, "X", -1), P(q, "Z", -1)),
            "z": (P(q, "X", -1), P(q, "Z")),
            "id": (P(q, "X"), P(q, "Z")),
        }[name]
        return {("X", q): table[0], ("Z", q): table[1]}
    if name == "cx":
        c, t = qubits
        return {
            ("X", c): P(c, "X") * P(t, "X"),
            ("Z", c): P(c, "Z"),
            ("X", t): P(t, "X"),
            ("Z", t): P(c, "Z") * P(t, "Z"),
        }
    if name == "cz":
        a, b = qubits
        return {
            ("X", a): P(a, "X") * P(b, "Z"),
            ("Z", a): P(a, "Z"),
            ("X", b): P(a, "Z") * P(b, "X"),
            ("Z", b): P(b, "Z"),
        }
    if name == "swap":
        a, b = qubits
        return {("X", a): P(b, "X"), ("Z", a): P(b, "Z"), ("X", b): P(a, "X"), ("Z", b): P(a, "Z")}
    raise ValueError(f"gate {name!r} is not a supported Clifford")


CLIFFORD_GATES = frozenset({"h", "s", "sdg", "x", "y", "z", "id", "cx", "cz", "swap"})


def conjugate(p: Pauli, name: str, qubits: Sequence[int]) -> Pauli:
    """Return ``U p U^dagger`` for a Clifford gate ``U``."""
    n = p.n
    imgs = _images(name, qubits, n)
    touched = set(qubits)
    # Split p = phase * (untouched part) * prod_{q in touched} X_q^{x} Z_q^{z}
    # using Y = i X Z, then map each factor.
    base_ops = ["I" if q in touched else c for q, c in enumerate(p.ops)]
    out = Pauli(p.phase, "".join(base_ops))
    for q in qubits:
        c = p.ops[q]
        if c == "I":
            continue
        if c == "X":
            out = out * imgs[("X", q)]
        elif c == "Z":
            out = out * imgs[("Z", q)]
        else:  # Y = i X Z
            out = Pauli(1j, "I" * n) * out * imgs[("X", q)] * imgs[("Z", q)]
    return out


def stabilizer_generators(n: int, gates: Iterable[tuple]) -> list[Pauli]:
    """Stabilizer generators of ``U|0...0>`` for a Clifford circuit ``U``.

    ``gates`` is an iterable of ``(name, qubits, params)`` tuples.
    """
    gens = [Pauli.single(n, q, "Z") for q in range(n)]
    for name, qubits, _params in gates:
        if name not in CLIFFORD_GATES:
            raise ValueError(f"non-Clifford gate {name!r} in stabilizer circuit")
        gens = [conjugate(g, name, qubits) for g in gens]
    return gens


class StabilizerGroup:
    """The full stabilizer group of a pure stabilizer state (exhaustive, n <= 12).

    Each element is indexed by a bit vector ``c`` over the generators, and its
    eigenvalue on the syndrome state ``|psi_s>`` is ``(-1)^{c.s}``.
    """

    def __init__(self, generators: Sequence[Pauli]):
        self.generators = list(generators)
        self.n = generators[0].n
        m = len(generators)
        if m != self.n:
            raise ValueError("need exactly n independent generators for a pure state")
        for i in range(m):
            for j in range(i + 1, m):
                if not generators[i].commutes(generators[j]):
                    raise ValueError("generators do not commute")
        coeffs = np.array(
            [[(k >> (m - 1 - i)) & 1 for i in range(m)] for k in range(2**m)], dtype=np.uint8
        )
        elements = []
        for c in coeffs:
            e = Pauli.identity(self.n)
            for i, bit in enumerate(c):
                if bit:
                    e = e * generators[i]
            if not e.is_hermitian():
                raise ValueError("generators do not form a valid stabilizer group")
            elements.append(e)
        if len({e.ops for e in elements}) != 2**m:
            raise ValueError("generators are not independent")
        if any(e.ops == "I" * self.n and e.phase != 1 for e in elements):
            raise ValueError("-I in group: generators stabilize no state")
        self.coeffs = coeffs  # (2^n, n) generator-combination vectors
        self.elements = elements

    def __len__(self) -> int:
        return len(self.elements)

    def projector(self) -> np.ndarray:
        d = 2**self.n
        return sum(e.matrix() for e in self.elements) / d

    def compatible(self, setting: str) -> list[int]:
        """Indices of elements measurable with a local Pauli ``setting``."""
        idx = []
        for k, e in enumerate(self.elements):
            if all(c == "I" or c == s for c, s in zip(e.ops, setting)):
                idx.append(k)
        return idx

    def restricted(self, qubits: Sequence[int]) -> "StabilizerGroup":
        """Stabilizer group of the reduced state on ``qubits`` when it is pure.

        The reduced state of a stabilizer state is pure iff the elements
        supported inside ``qubits`` form a group of size ``2^{|qubits|}``.
        """
        qubits = list(qubits)
        others = [q for q in range(self.n) if q not in qubits]
        inside = [e for e in self.elements if all(e.ops[q] == "I" for q in others)]
        m = len(qubits)
        if len(inside) != 2**m:
            raise ValueError("reduced state on the observed qubits is not pure")
        gens = _independent_generators([e.restrict(qubits) for e in inside], m)
        return StabilizerGroup(gens)


def _symplectic(p: Pauli) -> np.ndarray:
    x = [c in "XY" for c in p.ops]
    z = [c in "ZY" for c in p.ops]
    return np.array(x + z, dtype=np.uint8)


def _independent_generators(elements: Sequence[Pauli], m: int) -> list[Pauli]:
    """Pick m independent elements (over GF(2) symplectic vectors)."""
    basis: list[np.ndarray] = []
    chosen: list[Pauli] = []
    pivots: list[int] = []
    for e in elements:
        v = _symplectic(e).copy()
        for b, piv in zip(basis, pivots):
            if v[piv]:
                v ^= b
        nz = np.flatnonzero(v)
        if nz.size == 0:
            continue
        piv = int(nz[0])
        for i, b in enumerate(basis):
            if b[piv]:
                basis[i] = b ^ v
        basis.append(v)
        pivots.append(piv)
        chosen.append(e)
        if len(chosen) == m:
            break
    if len(chosen) != m:
        raise ValueError("could not find independent generators")
    return chosen
