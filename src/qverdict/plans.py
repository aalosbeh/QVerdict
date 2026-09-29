"""Targets, measurement plans and the exact case statistics oracles consume.

A *target* is the pure state |psi> that a contract refers to, on the observed
qubits of a program.  Two target classes are supported:

* ``stabilizer`` -- |psi> is a stabilizer state (Clifford specification);
* ``product``    -- |psi> is a product state (e.g. QFT of a basis input),
  which a single local setting identifies exactly.

A *plan* is a list of local tests.  For stabilizer targets the cover plan is
obtained by colouring the generators so that each colour class is qubit-wise
commuting; each colour defines one local Pauli setting whose test checks every
stabilizer element compatible with that setting.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np

from .circuits import Circuit
from .identify import PatternAtoms, pattern_atoms
from .pauli import Pauli, StabilizerGroup, stabilizer_generators
from .simulator import (
    NoiseModel,
    IDEAL,
    _TO_Z,
    apply_readout,
    basis_distribution,
    bit_table,
    density_matrix,
    partial_trace,
    statevector,
)


# ------------------------------------------------------------------ targets
@dataclass
class Target:
    kind: str                      # "stabilizer" or "product"
    m: int                         # number of observed qubits
    psi: np.ndarray                # target state on the observed qubits
    group: Optional[StabilizerGroup] = None
    rotations: Optional[list] = None  # product targets: U_q |phi_q> = |0>

    @property
    def dim(self) -> int:
        return 2**self.m


def make_target(spec: Circuit, observed: Sequence[int]) -> Target:
    """Build the contract target from an ideal specification circuit."""
    observed = list(observed)
    n = spec.n
    psi_full = statevector(spec)
    rho = partial_trace(np.outer(psi_full, psi_full.conj()), observed, n)
    evals, evecs = np.linalg.eigh(rho)
    if evals[-1] < 1 - 1e-9:
        raise ValueError("the specification's observed state is not pure")
    psi = evecs[:, -1]
    m = len(observed)
    if spec.is_clifford():
        full = StabilizerGroup(stabilizer_generators(n, spec.gates))
        group = full.restricted(observed) if m < n else full
        return Target("stabilizer", m, psi, group=group)
    # product target: every single-qubit marginal must be pure
    rots = []
    for q in range(m):
        r = partial_trace(np.outer(psi, psi.conj()), [q], m)
        w, v = np.linalg.eigh(r)
        if w[-1] < 1 - 1e-9:
            raise ValueError("non-Clifford targets must be product states")
        phi = v[:, -1]
        # unitary mapping phi -> |0>: rows are <phi| and its orthogonal complement
        perp = np.array([-np.conj(phi[1]), np.conj(phi[0])])
        U = np.vstack([phi.conj(), perp.conj()])
        rots.append(U)
    return Target("product", m, psi, rotations=rots)


# -------------------------------------------------------------------- tests
@dataclass
class Test:
    """A local test: measure with ``rotations`` then accept iff ``accept[b]``."""

    setting: str                    # human-readable label (Pauli letters or "U")
    rotations: list
    accept: np.ndarray              # (2^m,) bool
    coeffs: np.ndarray = field(default_factory=lambda: np.zeros((0, 0), dtype=np.uint8))
    element_vals: Optional[np.ndarray] = None  # (E, 2^m) +-1 values of checked elements


def stabilizer_test(group: StabilizerGroup, setting: str) -> Test:
    m = group.n
    idx = [k for k in group.compatible(setting) if group.elements[k].ops != "I" * m]
    bits = bit_table(m).astype(np.int64)
    vals = []
    for k in idx:
        e = group.elements[k]
        supp = np.array([c != "I" for c in e.ops], dtype=np.int64)
        parity = (bits @ supp) % 2
        vals.append(e.sign() * (1 - 2 * parity))
    vals = np.array(vals, dtype=np.int8).reshape(len(idx), 2**m)
    accept = (vals == 1).all(axis=0) if len(idx) else np.ones(2**m, dtype=bool)
    return Test(setting, [_TO_Z[c] for c in setting], accept,
                coeffs=group.coeffs[idx], element_vals=vals)


def cover_settings(group: StabilizerGroup) -> list[str]:
    """Greedy qubit-wise-commuting colouring of the generators -> local settings."""
    gens = group.generators
    m = group.n

    def qwc(a: Pauli, b: Pauli) -> bool:
        return all(x == "I" or y == "I" or x == y for x, y in zip(a.ops, b.ops))

    # colour generators in order of decreasing weight (Welsh-Powell)
    order = sorted(range(len(gens)), key=lambda i: -gens[i].weight())
    colours: list[list[int]] = []
    for i in order:
        for c in colours:
            if all(qwc(gens[i], gens[j]) for j in c):
                c.append(i)
                break
        else:
            colours.append([i])
    settings = []
    for c in colours:
        s = ["Z"] * m
        for j in c:
            for q, l in enumerate(gens[j].ops):
                if l != "I":
                    s[q] = l
        settings.append("".join(s))
    # canonical order: the all-Z-like setting first when present
    settings.sort(key=lambda s: (-s.count("Z"), s))
    return settings


@dataclass
class Plan:
    name: str
    tests: list
    atoms: Optional[PatternAtoms] = None

    @property
    def k(self) -> int:
        return len(self.tests)

    @property
    def complete(self) -> bool:
        return bool(self.atoms.complete) if self.atoms is not None else True


def cover_plan(target: Target) -> Plan:
    if target.kind == "product":
        return product_plan(target)
    tests = [stabilizer_test(target.group, s) for s in cover_settings(target.group)]
    atoms = pattern_atoms([t.coeffs for t in tests], target.m)
    return Plan("cover", tests, atoms)


def z_plan(target: Target) -> Plan:
    if target.kind == "product":
        # Z-only information about a product target: the Z-marginal test is
        # incomplete unless every factor is a basis state.
        accept = np.ones(target.dim, dtype=bool)
        return Plan("z", [Test("Z" * target.m, [_TO_Z["Z"]] * target.m, accept)], None)
    t = stabilizer_test(target.group, "Z" * target.m)
    atoms = pattern_atoms([t.coeffs], target.m)
    return Plan("z", [t], atoms)


def product_plan(target: Target) -> Plan:
    accept = np.zeros(target.dim, dtype=bool)
    accept[0] = True
    return Plan("product", [Test("U" * target.m, list(target.rotations), accept)], None)


def full_pauli_plan(target: Target, settings: Sequence[str]) -> Plan:
    tests = [stabilizer_test(target.group, s) for s in settings]
    atoms = pattern_atoms([t.coeffs for t in tests], target.m)
    return Plan("custom", tests, atoms)


# ------------------------------------------------------- exact case summary
@dataclass
class Case:
    """Exact quantities for one (program variant, noise) pair."""

    F: float                        # fidelity with the target (ground truth)
    m: int
    kind: str
    cover_dists: np.ndarray         # (k, 2^m) measured distributions per cover test
    cover_accept: np.ndarray        # (k, 2^m) acceptance masks
    cover_vals: list                # per test: (E, 2^m) element values or None
    cover_complete: bool
    cover_q: np.ndarray             # (k,) failure probabilities (measured)
    z_q: float                      # failure probability of the Z-basis test
    z_complete: bool
    exact_p: float                  # success probability of one exact-plan shot
    exact_a: float                  # F = a p + b for the exact plan
    exact_b: float
    z_dist: np.ndarray              # measured computational-basis distribution
    z_expected: np.ndarray
    x_dist: np.ndarray              # measured all-X-basis distribution
    x_expected: np.ndarray
    inv_p0: float                   # inverse test: P(all zeros), noisy uncompute
    meta: dict = field(default_factory=dict)
    # readout-corrected DFE (stabilizer targets): exact <g> of every non-identity
    # element on the pre-measurement state, element supports, and per-qubit
    # symmetric (twirled) readout flip probabilities.
    elem_exp: Optional[np.ndarray] = None
    elem_supp: Optional[np.ndarray] = None
    readout_sym: Optional[np.ndarray] = None
    product_dist: Optional[np.ndarray] = None  # product targets: pre-readout test-basis distribution


def _readout_flips(m: int, readout) -> list:
    if readout is None:
        return [(0.0, 0.0)] * m
    if isinstance(readout, (int, float)):
        return [(float(readout), float(readout))] * m
    return list(readout)


def pauli_expectation(rho: np.ndarray, p: Pauli) -> float:
    """tr(p rho) via  sum_y omega(y) rho[y, y xor a]  (exact, O(4^m) worst case)."""
    m = p.n
    bits = bit_table(m)
    xmask = np.array([c in "XY" for c in p.ops], dtype=np.uint8)
    y = bits
    flipped = y ^ xmask
    idx_y = np.arange(2**m)
    idx_f = (flipped * (1 << (m - 1 - np.arange(m)))).sum(axis=1)
    omega = np.full(2**m, complex(p.phase))
    for q, c in enumerate(p.ops):
        if c == "Z":
            omega *= np.where(y[:, q] == 1, -1, 1)
        elif c == "Y":
            omega *= 1j * np.where(y[:, q] == 1, -1, 1)
    return float(np.real(np.sum(omega * rho[idx_y, idx_f])))


def exact_case(program: Circuit, spec: Circuit, observed: Sequence[int], target: Target,
               plan: Plan, noise: NoiseModel = IDEAL, readout=None,
               rho_full: Optional[np.ndarray] = None,
               inverse_rho: Optional[np.ndarray] = None) -> Case:
    """Compute every exact probability the oracles need for one program variant."""
    m = target.m
    if rho_full is None:
        rho_full = density_matrix(program, noise)
    n = int(round(np.log2(rho_full.shape[0])))  # width of the supplied state
    rho = partial_trace(rho_full, observed, n)
    F = float(np.real(target.psi.conj() @ rho @ target.psi))
    flips = _readout_flips(m, readout if readout is not None else (noise.readout or None))

    def measured(rotations):
        return apply_readout(basis_distribution(rho, rotations), flips)

    dists = np.array([measured(t.rotations) for t in plan.tests])
    accept = np.array([t.accept for t in plan.tests])
    q = np.clip(1.0 - (dists * accept).sum(axis=1), 0.0, 1.0)
    zp = z_plan(target)
    zdist = measured([_TO_Z["Z"]] * m)
    z_q = float(np.clip(1.0 - (zdist * zp.tests[0].accept).sum(), 0.0, 1.0))
    xdist = measured([_TO_Z["X"]] * m)
    tpsi = np.outer(target.psi, target.psi.conj())
    z_exp = basis_distribution(tpsi, [_TO_Z["Z"]] * m)
    x_exp = basis_distribution(tpsi, [_TO_Z["X"]] * m)

    D = 2**m
    if target.kind == "stabilizer":
        # One DFE shot: uniformly random non-identity stabilizer element g,
        # measured in its own local setting; success iff the observed sign is +1.
        if all(f == (0.0, 0.0) for f in flips):
            Fp = (D * F - 1.0) / (D - 1.0)
            p = 0.5 * (1.0 + Fp)
        else:
            vals = []
            for e in target.group.elements:
                if e.ops == "I" * m:
                    continue
                setting = "".join(c if c != "I" else "Z" for c in e.ops)
                dist = measured([_TO_Z[c] for c in setting])
                supp = np.array([c != "I" for c in e.ops], dtype=np.int64)
                par = (bit_table(m).astype(np.int64) @ supp) % 2
                vals.append(e.sign() * float(np.sum(dist * (1 - 2 * par))))
            p = 0.5 * (1.0 + float(np.mean(vals)))
        a, b = 2.0 * (D - 1.0) / D, -(D - 2.0) / D
    else:
        p = float(dists[0][0]) if plan.name == "product" else float(measured(target.rotations)[0])
        a, b = 1.0, 0.0

    if inverse_rho is not None:
        inv_red = inverse_rho
        n_inv = int(round(np.log2(inv_red.shape[0])))
        p0 = float(apply_readout(np.real(np.diag(inv_red)).clip(0), _readout_flips(n_inv, readout if readout is not None else (noise.readout or None)))[0])
    else:
        p0 = float("nan")

    elem_exp = elem_supp = None
    if target.kind == "stabilizer":
        els = [e for e in target.group.elements if e.ops != "I" * m]
        elem_exp = np.array([pauli_expectation(rho, e) for e in els])
        elem_supp = np.array([[c != "I" for c in e.ops] for e in els], dtype=bool)
    readout_sym = np.array([0.5 * (a + b) for a, b in flips])
    product_dist = basis_distribution(rho, target.rotations) if target.kind == "product" else None

    return Case(
        elem_exp=elem_exp, elem_supp=elem_supp, readout_sym=readout_sym, product_dist=product_dist,
        F=F, m=m, kind=target.kind,
        cover_dists=dists, cover_accept=accept,
        cover_vals=[t.element_vals for t in plan.tests],
        cover_complete=plan.complete, cover_q=q,
        z_q=z_q, z_complete=bool(zp.atoms.complete) if zp.atoms is not None else False,
        exact_p=float(np.clip(p, 0.0, 1.0)), exact_a=a, exact_b=b,
        z_dist=zdist, z_expected=z_exp, x_dist=xdist, x_expected=x_exp,
        inv_p0=float(np.clip(p0, 0.0, 1.0)) if p0 == p0 else p0,
    )
