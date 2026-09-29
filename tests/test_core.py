"""Correctness tests for the algebra, simulator, bounds and confidence sequences."""
import itertools

import numpy as np
import pytest

from qverdict.benchmark import default_suite
from qverdict.circuits import Circuit
from qverdict.confseq import clopper_pearson_table, mixture_cs_table, mixture_cs_path
from qverdict.identify import lp_interval, pattern_atoms, union_interval
from qverdict.pauli import Pauli, StabilizerGroup, conjugate, stabilizer_generators
from qverdict.plans import cover_plan, exact_case, make_target, pauli_expectation, z_plan
from qverdict.simulator import (NoiseModel, _depolarize, apply_readout, density_matrix,
                                gate_matrix, partial_trace, setting_distribution, statevector)

RNG = np.random.default_rng(12345)


def _embed(U, qubits, n):
    """Full 2^n matrix of a gate acting on ``qubits`` (big-endian)."""
    c = Circuit(n)
    full = np.zeros((2**n, 2**n), dtype=complex)
    for b in range(2**n):
        e = np.zeros(2**n, dtype=complex)
        e[b] = 1
        from qverdict.simulator import _apply_sv
        full[:, b] = _apply_sv(e, U, qubits, n)
    return full


@pytest.mark.parametrize("name,qubits", [("h", (1,)), ("s", (0,)), ("sdg", (2,)), ("x", (1,)),
                                         ("y", (0,)), ("z", (2,)), ("cx", (0, 2)), ("cx", (2, 1)),
                                         ("cz", (1, 2)), ("swap", (0, 1))])
def test_clifford_conjugation_matches_matrices(name, qubits):
    n = 3
    U = _embed(gate_matrix(name), qubits, n)
    for letters in itertools.product("IXYZ", repeat=n):
        for sign in (1, -1):
            p = Pauli(sign, "".join(letters))
            img = conjugate(p, name, qubits)
            assert np.allclose(U @ p.matrix() @ U.conj().T, img.matrix())


def test_pauli_multiplication_phases():
    for a, b in itertools.product("IXYZ", repeat=2):
        pa, pb = Pauli(1, a), Pauli(1, b)
        assert np.allclose((pa * pb).matrix(), pa.matrix() @ pb.matrix())


@pytest.mark.parametrize("subject", default_suite(), ids=lambda s: s.name)
def test_targets_are_stabilized(subject):
    tgt = make_target(subject.spec, subject.observed)
    rho = np.outer(tgt.psi, tgt.psi.conj())
    if tgt.kind == "stabilizer":
        for g in tgt.group.elements:
            assert abs(pauli_expectation(rho, g) - 1) < 1e-9
            assert np.isclose(np.real(tgt.psi.conj() @ g.matrix() @ tgt.psi), 1)
        assert np.allclose(tgt.group.projector(), rho)
    plan = cover_plan(tgt)
    case = exact_case(subject.spec, subject.spec, subject.observed, tgt, plan)
    assert np.isclose(case.F, 1.0)
    assert np.allclose(case.cover_q, 0.0, atol=1e-10)
    assert np.isclose(case.exact_p, 1.0)


def test_depolarizing_matches_qiskit_convention():
    n = 2
    psi = RNG.normal(size=4) + 1j * RNG.normal(size=4)
    psi /= np.linalg.norm(psi)
    rho = np.outer(psi, psi.conj())
    p = 0.3
    out = _depolarize(rho, p, [1], n)
    red = partial_trace(rho, [0], n)
    expected = (1 - p) * rho + p * np.kron(red, np.eye(2) / 2)
    assert np.allclose(out, expected)
    out2 = _depolarize(rho, p, [0, 1], n)
    assert np.allclose(out2, (1 - p) * rho + p * np.eye(4) / 4)


def test_density_matrix_is_valid_under_noise():
    s = default_suite()[3]  # Cluster-6
    rho = density_matrix(s.spec, NoiseModel(p1=0.01, p2=0.05, gamma=0.01, lam=0.01))
    assert np.isclose(np.trace(rho).real, 1)
    assert np.allclose(rho, rho.conj().T)
    assert np.linalg.eigvalsh(rho).min() > -1e-10


def test_readout_matrix():
    p = np.array([1.0, 0, 0, 0])
    out = apply_readout(p, [(0.1, 0.2), (0.0, 0.0)])
    assert np.allclose(out, [0.9, 0, 0.1, 0])


def _random_rho(m, rank=None):
    d = 2**m
    rank = rank or d
    A = RNG.normal(size=(d, rank)) + 1j * RNG.normal(size=(d, rank))
    rho = A @ A.conj().T
    return rho / np.trace(rho)


@pytest.mark.parametrize("subject", [s for s in default_suite() if s.name != "QFT-4"], ids=lambda s: s.name)
def test_bounds_contain_true_fidelity_for_random_states(subject):
    tgt = make_target(subject.spec, subject.observed)
    plan = cover_plan(tgt)
    for _ in range(25):
        rho = _random_rho(tgt.m, rank=int(RNG.integers(1, 3)))
        F = np.real(tgt.psi.conj() @ rho @ tgt.psi)
        q = np.array([1 - np.sum(setting_distribution(rho, t.setting) * t.accept) for t in plan.tests])
        L, U = union_interval(q, q, plan.complete)
        assert L - 1e-10 <= F <= U + 1e-10
        Llp, Ulp = lp_interval(plan.atoms, q, q)
        assert Llp - 1e-7 <= F <= Ulp + 1e-7
        assert L <= Llp + 1e-7 and Ulp <= U + 1e-7  # LP is at least as tight
        # DFE identity: F = mean over the full group of <g>
        vals = [pauli_expectation(rho, g) for g in tgt.group.elements]
        assert np.isclose(np.mean(vals), F)


def test_two_setting_lp_equals_union_bound():
    """Theorem 1(ii): for complete two-test plans the union bounds are exact."""
    s = default_suite()[1]  # GHZ-4
    tgt = make_target(s.spec, s.observed)
    plan = cover_plan(tgt)
    assert plan.k == 2 and plan.complete
    for q1, q2 in [(0.01, 0.02), (0.1, 0.3), (0.5, 0.2), (0.7, 0.6)]:
        L, U = union_interval(np.array([q1, q2]), np.array([q1, q2]), True)
        Llp, Ulp = lp_interval(plan.atoms, [q1, q2], [q1, q2])
        assert np.isclose(L, Llp) and np.isclose(U, Ulp)


def test_z_only_plan_is_incomplete_for_superposition_targets():
    for s in default_suite():
        tgt = make_target(s.spec, s.observed)
        zp = z_plan(tgt)
        if s.name.startswith("BV"):
            assert zp.atoms.complete
        elif tgt.kind == "stabilizer":
            assert not zp.atoms.complete
            # Proposition 1: identified lower bound is 0 even for the exact target
            assert lp_interval(zp.atoms, [0.0], [0.0])[0] == pytest.approx(0.0, abs=1e-9)


def test_mixture_cs_contains_mle_and_is_nested_in_unit_interval():
    for t in (1, 16, 100, 1000):
        lo, hi = mixture_cs_table(t, 0.05)
        S = np.arange(t + 1)
        assert np.all(lo <= S / t + 1e-12) and np.all(hi >= S / t - 1e-12)
        assert lo[0] == 0 and hi[-1] == 1
        assert np.all(np.diff(lo) >= -1e-12) and np.all(np.diff(hi) >= -1e-12)


def test_mixture_cs_is_wider_than_clopper_pearson():
    lo, hi = mixture_cs_table(512, 0.05)
    clo, chi = clopper_pearson_table(512, 0.05)
    assert np.all(lo <= clo + 1e-9) and np.all(hi >= chi - 1e-9)


@pytest.mark.parametrize("p", [0.02, 0.3, 0.5])
def test_mixture_cs_time_uniform_coverage(p):
    """Monte Carlo: the probability that the CS ever excludes p is <= alpha."""
    alpha, R, T, b = 0.1, 4000, 4096, 8
    rng = np.random.default_rng(7)
    times = b * np.arange(1, T // b + 1)
    cum = rng.binomial(b, p, size=(R, len(times))).cumsum(axis=1)
    lo, hi = mixture_cs_path(cum, times, alpha)
    miss = ((lo > p) | (hi < p)).any(axis=1).mean()
    se = np.sqrt(alpha * (1 - alpha) / R)
    assert miss <= alpha + 3 * se


def test_peeking_clopper_pearson_violates_coverage():
    """Re-using fixed-sample intervals at every look is not time-uniform."""
    alpha, R, b = 0.05, 4000, 8
    rng = np.random.default_rng(11)
    times = b * np.arange(1, 513)
    cum = rng.binomial(b, 0.3, size=(R, len(times))).cumsum(axis=1)
    miss = np.zeros(R, dtype=bool)
    for j, t in enumerate(times):
        lo, hi = clopper_pearson_table(int(t), alpha)
        miss |= (lo[cum[:, j]] > 0.3) | (hi[cum[:, j]] < 0.3)
    assert miss.mean() > 2 * alpha


@pytest.mark.parametrize("mu", [0.1, 0.5, 0.93])
def test_empirical_bernstein_cs_time_uniform_coverage(mu):
    from qverdict.confseq import eb_cs_path
    alpha, R, T = 0.1, 3000, 2048
    rng = np.random.default_rng(3)
    X = rng.beta(10 * mu, 10 * (1 - mu), size=(R, T))
    lo, hi = eb_cs_path(X, alpha)
    miss = ((lo > mu) | (hi < mu)).any(axis=1).mean()
    assert miss <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / R)
