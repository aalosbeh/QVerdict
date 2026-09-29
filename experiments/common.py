"""Shared configuration and helpers for all experiments."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qverdict.oracles import FAIL, INC, PASS, OracleConfig  # noqa: E402
from qverdict.simulator import NoiseModel  # noqa: E402

RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

TAU = 0.90
ALPHA = 0.05
BUDGET = 8192
MASTER_SEED = 20260926

NOISE = {
    "N0": NoiseModel(name="N0"),
    # depolarizing only, typical of current superconducting two-qubit gates
    "N1": NoiseModel(p1=1e-3, p2=1e-2, name="N1"),
    # stronger, non-unital: depolarizing + amplitude damping + dephasing
    "N2": NoiseModel(p1=2e-3, p2=2e-2, gamma=5e-3, lam=5e-3, name="N2"),
}

MUTANT_CAPS = {"QGD": 30, "QGI": 40, "QGR": 30, "RGI": 30}

PROPOSED = ["QV-Z", "QV-TG", "QV-DFE", "QV-ESC"]
BASELINES = ["Z-chi2", "ZX-chi2", "Inverse-0tol", "Pauli-tol", "Plugin-DFE"]
CERTIFIED_FIXED = ["CP-TG", "CP-DFE"]
INVALID = ["Peek-CP-TG"]
ALL_ORACLES = BASELINES + CERTIFIED_FIXED + INVALID + PROPOSED


def config(**kw) -> OracleConfig:
    base = dict(budget=BUDGET, alpha=ALPHA, tau=TAU)
    base.update(kw)
    return OracleConfig(**base)


def seed_for(*parts) -> int:
    h = hashlib.sha256(("|".join(map(str, (MASTER_SEED,) + parts))).encode()).hexdigest()
    return int(h[:16], 16)


def summarize(v: np.ndarray, shots: np.ndarray, settings: np.ndarray, truth: bool) -> dict:
    R = len(v)
    npass, nfail, ninc = int((v == PASS).sum()), int((v == FAIL).sum()), int((v == INC).sum())
    wrong = nfail if truth else npass
    # unbiased estimate of P(two independent runs give opposite decisive verdicts)
    flip = 2.0 * npass * nfail / (R * (R - 1)) if R > 1 else 0.0
    return dict(R=R, n_pass=npass, n_fail=nfail, n_inc=ninc, n_wrong=wrong,
                p_pass=npass / R, p_fail=nfail / R, p_inc=ninc / R, p_wrong=wrong / R,
                flip=flip, shots_mean=float(shots.mean()), shots_median=float(np.median(shots)),
                shots_p90=float(np.percentile(shots, 90)), settings_mean=float(settings.mean()))


def environment() -> dict:
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "platform": platform.platform(), "machine": platform.machine(),
            "cpu_count": os.cpu_count()}


def write_json(name: str, payload) -> Path:
    p = RESULTS / name
    p.write_text(json.dumps(payload, indent=2, default=float))
    return p
