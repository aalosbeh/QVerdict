"""Exact state-vector and density-matrix simulation with gate-level noise.

Qubit 0 is the first tensor factor (big-endian): basis index ``b_0 b_1 ... b_{n-1}``
read as a binary number with ``b_0`` most significant.  The depolarizing
channel follows the Qiskit convention
``E(rho) = (1 - p) rho + p Tr_k(rho) (x) I / 2^k`` on the ``k`` touched qubits.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .circuits import Circuit

SQ2 = np.sqrt(2.0)
_FIXED = {
    "id": np.eye(2, dtype=complex),
    "h": np.array([[1, 1], [1, -1]], dtype=complex) / SQ2,
    "x": np.array([[0, 1], [1, 0]], dtype=complex),
    "y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "z": np.diag([1, -1]).astype(complex),
    "s": np.diag([1, 1j]).astype(complex),
    "sdg": np.diag([1, -1j]).astype(complex),
    "t": np.diag([1, np.exp(1j * np.pi / 4)]).astype(complex),
    "tdg": np.diag([1, np.exp(-1j * np.pi / 4)]).astype(complex),
    "cx": np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex),
    "cz": np.diag([1, 1, 1, -1]).astype(complex),
    "swap": np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex),
}


def gate_matrix(name: str, params: Sequence[float] = ()) -> np.ndarray:
    if name in _FIXED:
        return _FIXED[name]
    (th,) = params
    c, s = np.cos(th / 2), np.sin(th / 2)
    if name == "rx":
        return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)
    if name == "ry":
        return np.array([[c, -s], [s, c]], dtype=complex)
    if name == "rz":
        return np.diag([np.exp(-1j * th / 2), np.exp(1j * th / 2)]).astype(complex)
    if name == "p":
        return np.diag([1, np.exp(1j * th)]).astype(complex)
    if name == "cp":
        return np.diag([1, 1, 1, np.exp(1j * th)]).astype(complex)
    raise ValueError(f"unknown gate {name!r}")


# ------------------------------------------------------------------ noise model
@dataclass(frozen=True)
class NoiseModel:
    """Gate-level Markovian noise applied after every non-ideal gate.

    p1, p2 : depolarizing probability after one- and two-qubit gates.
    gamma  : amplitude-damping probability per touched qubit per gate.
    lam    : pure-dephasing probability per touched qubit per gate.
    readout: symmetric classical bit-flip probability at measurement.
    """

    p1: float = 0.0
    p2: float = 0.0
    gamma: float = 0.0
    lam: float = 0.0
    readout: float = 0.0
    name: str = "custom"

    def is_ideal(self) -> bool:
        return self.p1 == self.p2 == self.gamma == self.lam == 0.0


IDEAL = NoiseModel(name="ideal")


# ---------------------------------------------------------- tensor utilities
def _apply_sv(psi: np.ndarray, U: np.ndarray, qubits: Sequence[int], n: int) -> np.ndarray:
    k = len(qubits)
    t = psi.reshape((2,) * n)
    Ut = U.reshape((2,) * (2 * k))
    t = np.tensordot(Ut, t, axes=(list(range(k, 2 * k)), list(qubits)))
    t = np.moveaxis(t, list(range(k)), list(qubits))
    return t.reshape(-1)


def _apply_dm(rho: np.ndarray, U: np.ndarray, qubits: Sequence[int], n: int) -> np.ndarray:
    k = len(qubits)
    t = rho.reshape((2,) * (2 * n))
    Ut = U.reshape((2,) * (2 * k))
    t = np.tensordot(Ut, t, axes=(list(range(k, 2 * k)), list(qubits)))
    t = np.moveaxis(t, list(range(k)), list(qubits))
    cols = [q + n for q in qubits]
    t = np.tensordot(t, Ut.conj(), axes=(cols, list(range(k, 2 * k))))
    t = np.moveaxis(t, list(range(2 * n - k, 2 * n)), cols)
    return t.reshape(2**n, 2**n)


def _kraus(rho: np.ndarray, ks: Sequence[np.ndarray], qubits: Sequence[int], n: int) -> np.ndarray:
    return sum(_apply_dm(rho, K, qubits, n) for K in ks)


def _depolarize(rho: np.ndarray, p: float, qubits: Sequence[int], n: int) -> np.ndarray:
    if p <= 0:
        return rho
    k = len(qubits)
    t = rho.reshape((2,) * (2 * n))
    # partial trace over the touched qubits
    others = [q for q in range(n) if q not in qubits]
    perm = list(qubits) + others + [q + n for q in qubits] + [q + n for q in others]
    tp = np.transpose(t, perm).reshape(2**k, 2 ** (n - k), 2**k, 2 ** (n - k))
    red = np.einsum("iaib->ab", tp)
    mixed = np.einsum("ij,ab->iajb", np.eye(2**k) / 2**k, red)
    mixed = mixed.reshape((2,) * (2 * n))
    inv = np.argsort(perm)
    mixed = np.transpose(mixed, inv).reshape(2**n, 2**n)
    return (1 - p) * rho + p * mixed


def _amp_damp_kraus(g: float):
    return [np.array([[1, 0], [0, np.sqrt(1 - g)]], dtype=complex),
            np.array([[0, np.sqrt(g)], [0, 0]], dtype=complex)]


def _dephase_kraus(lam: float):
    return [np.sqrt(1 - lam) * np.eye(2, dtype=complex),
            np.sqrt(lam) * np.diag([1, 0]).astype(complex),
            np.sqrt(lam) * np.diag([0, 1]).astype(complex)]


# ------------------------------------------------------------------ simulate
def statevector(circ: Circuit) -> np.ndarray:
    n = circ.n
    psi = np.zeros(2**n, dtype=complex)
    psi[0] = 1.0
    for name, qubits, params in circ.gates:
        psi = _apply_sv(psi, gate_matrix(name, params), qubits, n)
    return psi


def density_matrix(circ: Circuit, noise: NoiseModel = IDEAL, rho0: np.ndarray | None = None) -> np.ndarray:
    """Final density matrix of ``circ`` under ``noise`` (readout excluded).

    ``rho0`` optionally replaces the initial state |0...0><0...0|.
    """
    n = circ.n
    if noise.is_ideal() and rho0 is None:
        psi = statevector(circ)
        return np.outer(psi, psi.conj())
    if rho0 is None:
        rho = np.zeros((2**n, 2**n), dtype=complex)
        rho[0, 0] = 1.0
    else:
        rho = np.array(rho0, dtype=complex)
    ad = _amp_damp_kraus(noise.gamma) if noise.gamma > 0 else None
    dp = _dephase_kraus(noise.lam) if noise.lam > 0 else None
    for i, (name, qubits, params) in enumerate(circ.gates):
        rho = _apply_dm(rho, gate_matrix(name, params), qubits, n)
        if i in circ.ideal:
            continue
        rho = _depolarize(rho, noise.p1 if len(qubits) == 1 else noise.p2, qubits, n)
        for q in qubits:
            if ad is not None:
                rho = _kraus(rho, ad, [q], n)
            if dp is not None:
                rho = _kraus(rho, dp, [q], n)
    return rho


def partial_trace(rho: np.ndarray, keep: Sequence[int], n: int) -> np.ndarray:
    keep = list(keep)
    if keep == list(range(n)):
        return rho
    drop = [q for q in range(n) if q not in keep]
    t = rho.reshape((2,) * (2 * n))
    perm = keep + drop + [q + n for q in keep] + [q + n for q in drop]
    k, d = len(keep), len(drop)
    tp = np.transpose(t, perm).reshape(2**k, 2**d, 2**k, 2**d)
    return np.einsum("aibi->ab", tp)


# --------------------------------------------------------------- measurement
_TO_Z = {
    "Z": np.eye(2, dtype=complex),
    "I": np.eye(2, dtype=complex),
    "X": _FIXED["h"],
    "Y": _FIXED["h"] @ _FIXED["sdg"],
}


def basis_distribution(rho: np.ndarray, rotations: Sequence[np.ndarray]) -> np.ndarray:
    """Outcome distribution after applying single-qubit ``rotations`` then Z-measurement."""
    m = len(rotations)
    for q, U in enumerate(rotations):
        if not np.allclose(U, np.eye(2)):
            rho = _apply_dm(rho, U, [q], m)
    p = np.real(np.diag(rho)).copy()
    p[p < 0] = 0.0
    return p / p.sum()


def setting_distribution(rho: np.ndarray, setting: str) -> np.ndarray:
    """Distribution of outcome bits when qubit q is measured in Pauli ``setting[q]``.

    Bit 0 on qubit q corresponds to the +1 eigenvalue of ``setting[q]``.
    """
    return basis_distribution(rho, [_TO_Z[c] for c in setting])


def apply_readout(p: np.ndarray, flips: Sequence[tuple[float, float]]) -> np.ndarray:
    """Apply independent per-qubit readout errors.

    ``flips[q] = (p10, p01)`` with p10 = P(read 1 | 0), p01 = P(read 0 | 1).
    """
    m = len(flips)
    t = p.reshape((2,) * m)
    for q, (p10, p01) in enumerate(flips):
        if p10 == 0 and p01 == 0:
            continue
        A = np.array([[1 - p10, p01], [p10, 1 - p01]])
        t = np.moveaxis(np.tensordot(A, t, axes=([1], [q])), 0, q)
    return t.reshape(-1)


def bit_table(m: int) -> np.ndarray:
    """(2^m, m) array of bits; row b gives the bits of basis index b (qubit 0 first)."""
    idx = np.arange(2**m)
    return ((idx[:, None] >> (m - 1 - np.arange(m))[None, :]) & 1).astype(np.uint8)
