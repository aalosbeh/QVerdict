"""First-order mutation operators for gate-list circuits.

Operators follow the categories used by Muskit/QMutPy-style tools and by
Miranskyy et al. (2025): gate deletion (QGD), gate insertion (QGI), gate
replacement (QGR) and small-rotation insertion (RGI, coherent errors).  Only
non-ideal gates are mutated and insertions act on program qubits only.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .circuits import Circuit, gate

ONEQ = ("x", "y", "z", "h", "s", "sdg", "t")
RGI_ANGLES = (np.pi / 16, np.pi / 8, np.pi / 4)


@dataclass
class Mutant:
    op: str
    desc: str
    circuit: Circuit


def _program_qubits(c: Circuit) -> list[int]:
    qs = set()
    for i in c.mutable_indices():
        qs.update(c.gates[i][1])
    return sorted(qs)


def _replace(c: Circuit, i: int, new: list) -> Circuit:
    out = c.copy()
    out.gates = c.gates[:i] + new + c.gates[i + 1:]
    shift = len(new) - 1
    out.ideal = {j if j < i else j + shift for j in c.ideal if j != i}
    return out


def _insert(c: Circuit, pos: int, g) -> Circuit:
    out = c.copy()
    out.gates = c.gates[:pos] + [g] + c.gates[pos:]
    out.ideal = {j if j < pos else j + 1 for j in c.ideal}
    return out


def _alternatives(g):
    name, qs, params = g
    if len(qs) == 1:
        return [gate(a, *qs) for a in ONEQ if a != name]
    a, b = qs
    alts = {
        "cx": [gate("cz", a, b), gate("cx", b, a), gate("swap", a, b)],
        "cz": [gate("cx", a, b), gate("cx", b, a), gate("swap", a, b)],
        "swap": [gate("cx", a, b), gate("cz", a, b)],
        "cp": [gate("cz", a, b), gate("cp", a, b, params=[params[0] / 2]) if params else None,
               gate("cp", a, b, params=[2 * params[0]]) if params else None],
    }[name]
    return [x for x in alts if x is not None]


def enumerate_mutants(c: Circuit) -> dict[str, list[Mutant]]:
    idx = c.mutable_indices()
    qubits = _program_qubits(c)
    start = min(idx) if idx else len(c.gates)
    positions = list(range(start, len(c.gates) + 1))
    out: dict[str, list[Mutant]] = {"QGD": [], "QGI": [], "QGR": [], "RGI": []}
    for i in idx:
        out["QGD"].append(Mutant("QGD", f"delete {c.gates[i][0]}{c.gates[i][1]} @{i}", _replace(c, i, [])))
        for alt in _alternatives(c.gates[i]):
            out["QGR"].append(Mutant("QGR", f"{c.gates[i][0]}{c.gates[i][1]}->{alt[0]}{alt[1]} @{i}",
                                     _replace(c, i, [alt])))
    for pos in positions:
        for q in qubits:
            for a in ONEQ:
                out["QGI"].append(Mutant("QGI", f"insert {a}({q}) @{pos}", _insert(c, pos, gate(a, q))))
            for axis in ("rz", "rx"):
                for th in RGI_ANGLES:
                    out["RGI"].append(Mutant("RGI", f"insert {axis}({th:.4f})({q}) @{pos}",
                                             _insert(c, pos, gate(axis, q, params=[th]))))
    return out


def sample_mutants(c: Circuit, caps: dict[str, int], seed: int) -> list[Mutant]:
    """Seeded sample of at most ``caps[op]`` mutants per operator (deduplicated)."""
    rng = np.random.default_rng(seed)
    pool = enumerate_mutants(c)
    chosen: list[Mutant] = []
    seen = set()
    for op in ("QGD", "QGI", "QGR", "RGI"):
        items = pool[op]
        order = rng.permutation(len(items))
        taken = 0
        for k in order:
            m = items[int(k)]
            key = tuple(m.circuit.gates)
            if key in seen or key == tuple(c.gates):
                continue
            seen.add(key)
            chosen.append(m)
            taken += 1
            if taken >= caps.get(op, 0):
                break
    return chosen
