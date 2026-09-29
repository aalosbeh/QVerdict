"""Identified fidelity intervals of stabilizer measurement plans.

For a stabilizer target |psi> with group S and a plan of tests, each test j
accepts iff every element of a subgroup G_j <= S compatible with its local
setting evaluates to +1.  Twirling by S leaves the fidelity and every test's
acceptance probability unchanged and maps any state to a mixture of syndrome
states |psi_s>, s in GF(2)^n.  Test j accepts |psi_s> iff c.s = 0 for all
generator-combination vectors c of G_j.  Hence the set of fidelities that are
consistent with (exact or interval) failure probabilities is the value range of
a small linear programme over the *failure patterns* realisable by syndromes
(Theorem 1 in the paper).  This module computes that programme exactly and
its closed-form (Frechet / union) relaxation used by the sequential oracles.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy.optimize import linprog


@dataclass(frozen=True)
class PatternAtoms:
    """Distinct failure patterns of the plan's tests over nonzero syndromes."""

    patterns: np.ndarray  # (A, k) booleans: True = test fails on this atom
    complete: bool        # True iff only the zero syndrome passes all tests

    @property
    def k(self) -> int:
        return self.patterns.shape[1]


def pattern_atoms(test_coeffs: Sequence[np.ndarray], n: int) -> PatternAtoms:
    """Enumerate failure patterns.

    ``test_coeffs[j]`` is a (E_j, n) array of generator-combination vectors of
    the elements checked by test j.
    """
    s = ((np.arange(2**n)[:, None] >> (n - 1 - np.arange(n))[None, :]) & 1).astype(np.int64)
    s = s[1:]  # nonzero syndromes
    fails = []
    for C in test_coeffs:
        C = np.asarray(C, dtype=np.int64)
        if C.size == 0:
            fails.append(np.zeros(len(s), dtype=bool))
        else:
            fails.append(((s @ C.T) % 2).any(axis=1))
    F = np.stack(fails, axis=1)
    uniq = np.unique(F, axis=0)
    complete = not (~uniq).all(axis=1).any()
    return PatternAtoms(uniq, bool(complete))


def lp_interval(atoms: PatternAtoms, q_lo: Sequence[float], q_hi: Sequence[float]) -> tuple[float, float]:
    """Exact identified interval [L, U] of the fidelity given q_j in [q_lo_j, q_hi_j].

    Variables: mass on the target atom (index 0) and on each pattern atom.
    Returns (nan, nan) if the constraints are infeasible (inconsistent data).
    """
    P = atoms.patterns.astype(float)  # (A, k)
    A, k = P.shape
    nvar = 1 + A
    # sum of masses = 1
    A_eq = np.ones((1, nvar))
    b_eq = np.array([1.0])
    # q_lo_j <= sum_{atoms failing j} mass <= q_hi_j
    rows, rhs = [], []
    for j in range(k):
        row = np.concatenate([[0.0], P[:, j]])
        rows.append(row)
        rhs.append(q_hi[j])
        rows.append(-row)
        rhs.append(-q_lo[j])
    A_ub = np.array(rows)
    b_ub = np.array(rhs)
    c = np.zeros(nvar)
    c[0] = 1.0
    bounds = [(0, 1)] * nvar
    lo = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    hi = linprog(-c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    if lo.status != 0 or hi.status != 0:
        return float("nan"), float("nan")
    return float(lo.fun), float(-hi.fun)


def union_interval(q_lo: np.ndarray, q_hi: np.ndarray, complete: bool) -> tuple[np.ndarray, np.ndarray]:
    """Closed-form valid bounds (vectorised over leading axes; tests on the last axis).

    L = max(0, 1 - sum_j q_hi_j) if the plan is complete, else 0;
    U = 1 - max_j q_lo_j.
    Both are valid for any plan (Proposition 2); they coincide with the LP for
    complete two-test plans whose pass sets are not nested (Theorem 1).
    """
    q_lo = np.asarray(q_lo, dtype=float)
    q_hi = np.asarray(q_hi, dtype=float)
    U = 1.0 - q_lo.max(axis=-1)
    if complete:
        L = np.maximum(0.0, 1.0 - q_hi.sum(axis=-1))
    else:
        L = np.zeros_like(U)
    return L, U
