"""Behavioural tests of the oracles, including Monte Carlo soundness checks."""
import numpy as np
import pytest

from qverdict.benchmark import bell, ghz
from qverdict.circuits import Circuit
from qverdict.mutants import enumerate_mutants, sample_mutants
from qverdict.oracles import FAIL, INC, ORACLES, PASS, OracleConfig, run_oracle
from qverdict.plans import cover_plan, exact_case, make_target
from qverdict.simulator import NoiseModel


def _case(circuit, subject, noise=NoiseModel()):
    tgt = make_target(subject.spec, subject.observed)
    plan = cover_plan(tgt)
    return exact_case(circuit, subject.spec, subject.observed, tgt, plan, noise)


def test_phase_flip_is_invisible_to_z_chi2_but_caught_by_qv():
    s = bell()
    faulty = s.spec.copy().add("z", 0)
    case = _case(faulty, s)
    assert case.F < 1e-12
    cfg = OracleConfig(budget=2048)
    rng = np.random.default_rng(0)
    v, _, _ = run_oracle("Z-chi2", case, cfg, rng, 500)
    assert (v == PASS).mean() > 0.9  # phase-blind
    for name in ("QV-TG", "QV-DFE", "QV-ESC"):
        v, shots, _ = run_oracle(name, case, cfg, rng, 500)
        assert (v == FAIL).all()
        assert shots.mean() < 200


def test_qv_z_never_passes_superposition_targets():
    s = ghz(4)
    case = _case(s.spec, s)
    v, _, _ = run_oracle("QV-Z", case, OracleConfig(budget=4096), np.random.default_rng(1), 300)
    assert not (v == PASS).any()


@pytest.mark.parametrize("theta", [0.60, 0.6435, 0.70])
@pytest.mark.parametrize("name", ["QV-TG", "QV-DFE", "QV-ESC", "CP-TG", "CP-DFE"])
def test_certified_oracles_are_sound_near_threshold(theta, name):
    """Coherent phase error with F = cos^2(theta/2) straddling tau = 0.9."""
    s = bell()
    c = s.spec.copy().add("rz", 1, params=[theta])
    case = _case(c, s)
    truth = case.F >= 0.9 - 1e-12
    R = 3000
    v, _, _ = run_oracle(name, case, OracleConfig(budget=4096), np.random.default_rng(3), R)
    wrong = (v == FAIL) if truth else (v == PASS)
    alpha = 0.05
    assert wrong.mean() <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / R)


def test_mutants_are_distinct_and_respect_ideal_gates():
    s = ghz(4)
    pool = enumerate_mutants(s.spec)
    assert set(pool) == {"QGD", "QGI", "QGR", "RGI"}
    ms = sample_mutants(s.spec, {"QGD": 100, "QGI": 30, "QGR": 20, "RGI": 20}, seed=5)
    keys = [tuple(m.circuit.gates) for m in ms]
    assert len(keys) == len(set(keys))
    assert tuple(s.spec.gates) not in keys


def test_all_oracles_run_and_return_valid_codes():
    s = ghz(4)
    case = _case(s.spec, s, NoiseModel(p1=1e-3, p2=1e-2))
    for name in ORACLES:
        v, shots, k = run_oracle(name, case, OracleConfig(budget=1024), np.random.default_rng(2), 50)
        assert set(np.unique(v)).issubset({PASS, FAIL, INC})
        if name == "Pauli-tol" and case.kind != "stabilizer":
            continue
        assert (shots >= 1).all() and (shots <= 1024).all()


@pytest.mark.parametrize("r", [0.0, 0.03])
def test_readout_corrected_dfe_is_sound_near_threshold(r):
    s = ghz(4)
    c = s.spec.copy().add("rz", 0, params=[2 * np.arccos(np.sqrt(0.93))])
    tgt = make_target(s.spec, s.observed)
    case = exact_case(c, s.spec, s.observed, tgt, cover_plan(tgt), readout=r)
    assert case.F >= 0.9
    v, _, _ = run_oracle("QV-DFE-RC", case, OracleConfig(budget=8192), np.random.default_rng(9), 400)
    assert (v == FAIL).mean() <= 0.05 + 3 * np.sqrt(0.05 * 0.95 / 400)
    assert (v == PASS).mean() > 0.3


def test_readout_corrected_product_target_is_sound():
    from qverdict.benchmark import qft
    s = qft(4, 0b1011)
    tgt = make_target(s.spec, s.observed)
    c = s.spec.copy().add("rz", 0, params=[2 * np.arccos(np.sqrt(0.95))])
    case = exact_case(c, s.spec, s.observed, tgt, cover_plan(tgt), readout=0.03)
    assert case.kind == "product" and case.F >= 0.9
    v, _, _ = run_oracle("QV-DFE-RC", case, OracleConfig(budget=8192), np.random.default_rng(4), 300)
    assert (v == FAIL).mean() <= 0.05 + 3 * np.sqrt(0.05 * 0.95 / 300)
    assert (v == PASS).mean() > 0.3
