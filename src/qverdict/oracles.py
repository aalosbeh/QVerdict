"""Test oracles: proposed anytime-valid three-valued oracles and baselines.

Every oracle is vectorised over ``R`` independent repetitions and returns

* ``verdict``: int8 array, +1 = PASS, -1 = FAIL, 0 = INCONCLUSIVE;
* ``shots``:   int array, number of program executions consumed;
* ``settings``: float array, number of distinct measurement settings used.

Sampling is exact: each oracle draws binomial/multinomial/geometric counts
from the exact probabilities stored in a :class:`qverdict.plans.Case`.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import chi2 as chi2_dist

from .confseq import clopper_pearson_table, eb_cs_path, mixture_cs_path
from .identify import union_interval
from .plans import Case

PASS, FAIL, INC = 1, -1, 0


@dataclass(frozen=True)
class OracleConfig:
    budget: int = 8192        # maximum number of shots N
    alpha: float = 0.05       # error budget per verdict
    tau: float = 0.90         # fidelity threshold of the contract
    batch: int = 16           # shots per test between sequential looks
    esc_fraction: float = 0.25  # QV-ESC: maximum stage-1 share of the budget
    esc_warmup: int = 4         # QV-ESC: looks before predicted escalation
    prior: float = 0.5        # Beta(prior, prior) mixing distribution
    pauli_tol: float = 0.01   # QOPS-style tolerance
    cal_shots: int = 8192     # QV-DFE-RC: readout-calibration shots (amortised)


def _verdict_from_bounds(L, U, tau):
    return np.where(L >= tau, PASS, np.where(U < tau, FAIL, INC)).astype(np.int8)


def _first_true(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Index of the first True along axis 1 and whether any exists."""
    any_ = mask.any(axis=1)
    idx = np.where(any_, mask.argmax(axis=1), mask.shape[1] - 1)
    return idx, any_


def _expected_distinct(D_minus_1: int, draws: np.ndarray) -> np.ndarray:
    return D_minus_1 * (1.0 - (1.0 - 1.0 / D_minus_1) ** draws)


# ============================================================ baselines
def z_chi2(case: Case, cfg: OracleConfig, rng: np.random.Generator, R: int):
    """Computational-basis oracle (Quito/Muskit-style): unexpected-output check
    plus Pearson chi-square goodness of fit at level alpha."""
    return _chi2_basis(case.z_dist, case.z_expected, cfg.budget, cfg.alpha, rng, R), \
        np.full(R, cfg.budget), np.ones(R)


def zx_chi2(case: Case, cfg: OracleConfig, rng: np.random.Generator, R: int):
    """Projective-measurement extension: the same test in Z and in X^{(x)m},
    half of the budget each, Bonferroni alpha/2 per basis."""
    n1 = cfg.budget // 2
    vz = _chi2_basis(case.z_dist, case.z_expected, n1, cfg.alpha / 2, rng, R)
    vx = _chi2_basis(case.x_dist, case.x_expected, cfg.budget - n1, cfg.alpha / 2, rng, R)
    v = np.where((vz == FAIL) | (vx == FAIL), FAIL, PASS).astype(np.int8)
    return v, np.full(R, cfg.budget), np.full(R, 2.0)


def _chi2_basis(dist, expected, N, alpha, rng, R):
    counts = rng.multinomial(N, dist, size=R)
    zero = expected < 1e-12
    unexpected = counts[:, zero].sum(axis=1) > 0
    e = expected[~zero] * N
    o = counts[:, ~zero]
    stat = ((o - e) ** 2 / e).sum(axis=1)
    df = max(int((~zero).sum()) - 1, 0)
    if df == 0:
        reject = np.zeros(R, dtype=bool)
    else:
        reject = chi2_dist.sf(stat, df) < alpha
    return np.where(unexpected | reject, FAIL, PASS).astype(np.int8)


def inverse_zero_tol(case: Case, cfg: OracleConfig, rng: np.random.Generator, R: int):
    """Inverse test: run program then the inverse specification; FAIL at the
    first non-zero outcome, PASS if all ``budget`` outcomes are zero."""
    p_nonzero = max(0.0, 1.0 - case.inv_p0)
    if p_nonzero <= 0:
        return np.full(R, PASS, dtype=np.int8), np.full(R, cfg.budget), np.ones(R)
    first = rng.geometric(p_nonzero, size=R)
    v = np.where(first <= cfg.budget, FAIL, PASS).astype(np.int8)
    shots = np.minimum(first, cfg.budget)
    return v, shots, np.ones(R)


def pauli_tolerance(case: Case, cfg: OracleConfig, rng: np.random.Generator, R: int):
    """QOPS-style oracle: estimate the checked stabilizer expectations in the
    cover settings and PASS iff |expected - observed| <= tolerance."""
    if case.kind != "stabilizer":  # not applicable: no stabilizer test cases
        return np.full(R, INC, dtype=np.int8), np.zeros(R), np.zeros(R)
    k = len(case.cover_dists)
    per = cfg.budget // k
    sums = np.zeros(R)
    total = 0
    for j in range(k):
        vals = case.cover_vals[j]
        if vals is None or len(vals) == 0:
            continue
        counts = rng.multinomial(per, case.cover_dists[j], size=R)  # (R, 2^m)
        est = counts @ vals.T.astype(float) / per                  # (R, E)
        sums += est.sum(axis=1)
        total += vals.shape[0]
    obs = sums / max(total, 1)
    v = np.where(np.abs(1.0 - obs) <= cfg.pauli_tol, PASS, FAIL).astype(np.int8)
    return v, np.full(R, per * k), np.full(R, float(k))


def plugin_exact(case: Case, cfg: OracleConfig, rng: np.random.Generator, R: int):
    """Tolerance-aware but uncertainty-free: PASS iff the point estimate of
    the fidelity (exact plan) reaches tau."""
    S = rng.binomial(cfg.budget, case.exact_p, size=R)
    Fhat = case.exact_a * S / cfg.budget + case.exact_b
    v = np.where(Fhat >= cfg.tau, PASS, FAIL).astype(np.int8)
    return v, np.full(R, cfg.budget), _settings_exact(case, np.full(R, cfg.budget))


def _settings_exact(case: Case, shots):
    if case.kind != "stabilizer":
        return np.ones_like(shots, dtype=float)
    return _expected_distinct(2**case.m - 1, shots)


# ================================================ fixed-sample certified
def cp_cover(case: Case, cfg: OracleConfig, rng: np.random.Generator, R: int):
    k = len(case.cover_q)
    per = cfg.budget // k
    lo = np.empty((R, k))
    hi = np.empty((R, k))
    for j in range(k):
        f = rng.binomial(per, case.cover_q[j], size=R)
        tl, th = clopper_pearson_table(per, cfg.alpha / k)
        lo[:, j], hi[:, j] = tl[f], th[f]
    L, U = union_interval(lo, hi, case.cover_complete)
    return _verdict_from_bounds(L, U, cfg.tau), np.full(R, per * k), np.full(R, float(k))


def cp_exact(case: Case, cfg: OracleConfig, rng: np.random.Generator, R: int):
    S = rng.binomial(cfg.budget, case.exact_p, size=R)
    tl, th = clopper_pearson_table(cfg.budget, cfg.alpha)
    L = np.clip(case.exact_a * tl[S] + case.exact_b, 0, 1)
    U = np.clip(case.exact_a * th[S] + case.exact_b, 0, 1)
    return _verdict_from_bounds(L, U, cfg.tau), np.full(R, cfg.budget), \
        _settings_exact(case, np.full(R, cfg.budget))


# ================================================= sequential machinery
def _cover_paths(case: Case, cfg: OracleConfig, rng, R, n_rounds, alpha_each, anytime=True):
    """Failure-count paths and per-look bounds for the cover plan."""
    k = len(case.cover_q)
    b = cfg.batch
    times = b * np.arange(1, n_rounds + 1)
    los, his, cums = [], [], []
    for j in range(k):
        inc = rng.binomial(b, case.cover_q[j], size=(R, n_rounds))
        cum = inc.cumsum(axis=1)
        cums.append(cum)
        if anytime:
            lo, hi = mixture_cs_path(cum, times, alpha_each, cfg.prior, cfg.prior)
        else:  # fixed-sample Clopper-Pearson re-used at every look ("peeking")
            lo = np.empty((R, n_rounds))
            hi = np.empty((R, n_rounds))
            for r, t in enumerate(times):
                tl, th = clopper_pearson_table(int(t), alpha_each)
                lo[:, r], hi[:, r] = tl[cum[:, r]], th[cum[:, r]]
        los.append(lo)
        his.append(hi)
    lo = np.stack(los, axis=-1)
    hi = np.stack(his, axis=-1)
    L, U = union_interval(lo, hi, case.cover_complete)
    qhat = np.stack(cums, axis=-1) / times[None, :, None]
    return L, U, lo, hi, times * k, qhat


def _stop(L, U, shots_at, tau, budget_shots):
    decide = (L >= tau) | (U < tau)
    idx, any_ = _first_true(decide)
    rows = np.arange(L.shape[0])
    v = np.where(any_, _verdict_from_bounds(L[rows, idx], U[rows, idx], tau), INC).astype(np.int8)
    shots = np.where(any_, shots_at[idx], budget_shots)
    return v, shots


def qv_cover(case: Case, cfg: OracleConfig, rng, R):
    """QV-TG: anytime-valid sequential oracle on the cover (two-setting) plan."""
    k = len(case.cover_q)
    n_rounds = max(1, cfg.budget // (cfg.batch * k))
    L, U, _, _, shots_at, _ = _cover_paths(case, cfg, rng, R, n_rounds, cfg.alpha / k)
    v, shots = _stop(L, U, shots_at, cfg.tau, shots_at[-1])
    return v, shots, np.full(R, float(k))


def peek_cp_cover(case: Case, cfg: OracleConfig, rng, R):
    """Invalid sequential baseline: fixed-sample CP intervals checked at every look."""
    k = len(case.cover_q)
    n_rounds = max(1, cfg.budget // (cfg.batch * k))
    L, U, _, _, shots_at, _ = _cover_paths(case, cfg, rng, R, n_rounds, cfg.alpha / k, anytime=False)
    v, shots = _stop(L, U, shots_at, cfg.tau, shots_at[-1])
    return v, shots, np.full(R, float(k))


def qv_z(case: Case, cfg: OracleConfig, rng, R):
    """QV-Z: the sound oracle restricted to computational-basis data.

    Unless the target is a basis state it can only FAIL (Proposition 1)."""
    b = cfg.batch * 2
    n_rounds = max(1, cfg.budget // b)
    times = b * np.arange(1, n_rounds + 1)
    cum = rng.binomial(b, case.z_q, size=(R, n_rounds)).cumsum(axis=1)
    lo, hi = mixture_cs_path(cum, times, cfg.alpha, cfg.prior, cfg.prior)
    L, U = union_interval(lo[..., None], hi[..., None], case.z_complete)
    v, shots = _stop(L, U, times, cfg.tau, times[-1])
    return v, shots, np.ones(R)


def _exact_paths(case: Case, cfg: OracleConfig, rng, R, n_rounds, alpha):
    b = cfg.batch * 2
    times = b * np.arange(1, n_rounds + 1)
    cum = rng.binomial(b, case.exact_p, size=(R, n_rounds)).cumsum(axis=1)
    lo, hi = mixture_cs_path(cum, times, alpha, cfg.prior, cfg.prior)
    L = np.clip(case.exact_a * lo + case.exact_b, 0, 1)
    U = np.clip(case.exact_a * hi + case.exact_b, 0, 1)
    return L, U, times


def qv_exact(case: Case, cfg: OracleConfig, rng, R):
    """QV-DFE: anytime-valid sequential oracle on the exact plan (DFE for
    stabilizer targets, the product-basis test for product targets)."""
    n_rounds = max(1, cfg.budget // (cfg.batch * 2))
    L, U, times = _exact_paths(case, cfg, rng, R, n_rounds, cfg.alpha)
    v, shots = _stop(L, U, times, cfg.tau, times[-1])
    return v, shots, _settings_exact(case, shots)


def qv_escalate(case: Case, cfg: OracleConfig, rng, R):
    """QV-ESC: cover plan first; escalate to the exact plan when the cover plan
    is certified structurally inconclusive or its budget share is spent.

    Error budget: alpha/2 shared by the k cover tests, alpha/2 for the exact
    plan; all confidence sequences hold simultaneously with probability
    >= 1 - alpha, so every verdict is sound (Theorem 2)."""
    if case.kind != "stabilizer":
        return qv_exact(case, cfg, rng, R)
    k = len(case.cover_q)
    n1 = max(1, int(cfg.esc_fraction * cfg.budget) // (cfg.batch * k))
    L1, U1, lo, hi, shots_at, qhat = _cover_paths(case, cfg, rng, R, n1, cfg.alpha / (2 * k))
    decide = (L1 >= cfg.tau) | (U1 < cfg.tau)
    # (a) certified structural ambiguity: even the most favourable parameters in
    #     the confidence box cannot yield a verdict with this plan;
    if case.cover_complete:
        cannot_pass = 1.0 - lo.sum(axis=-1) < cfg.tau
        est_cannot_pass = 1.0 - qhat.sum(axis=-1) < cfg.tau
    else:
        cannot_pass = est_cannot_pass = np.ones_like(decide)
    cannot_fail = (1.0 - hi.max(axis=-1)) >= cfg.tau
    est_cannot_fail = (1.0 - qhat.max(axis=-1)) >= cfg.tau
    # (b) predicted ambiguity: after a warm-up, the running estimate places tau
    #     inside the plan's identified interval.  Escalation is a heuristic
    #     choice; it does not affect soundness (Theorem 2).
    warm = (np.arange(n1) + 1 >= cfg.esc_warmup)[None, :]
    escalate = (cannot_pass & cannot_fail) | (warm & est_cannot_pass & est_cannot_fail)
    stop1 = decide | escalate
    idx, any_ = _first_true(stop1)
    rows = np.arange(R)
    decided = any_ & decide[rows, idx]
    v = np.where(decided, _verdict_from_bounds(L1[rows, idx], U1[rows, idx], cfg.tau), INC).astype(np.int8)
    used = np.where(any_, shots_at[idx], shots_at[-1])
    settings = np.full(R, float(k))
    todo = ~decided
    if todo.any():
        remaining = cfg.budget - used[todo]
        n2 = max(1, int(remaining.max()) // (cfg.batch * 2))
        L2, U2, times = _exact_paths(case, cfg, rng, int(todo.sum()), n2, cfg.alpha / 2)
        # intersect with the frozen stage-1 bounds
        Lf = np.maximum(L2, L1[rows, idx][todo][:, None])
        Uf = np.minimum(U2, U1[rows, idx][todo][:, None])
        valid = times[None, :] <= remaining[:, None]
        dec2 = ((Lf >= cfg.tau) | (Uf < cfg.tau)) & valid
        j2, any2 = _first_true(dec2)
        r2 = np.arange(int(todo.sum()))
        v2 = np.where(any2, _verdict_from_bounds(Lf[r2, j2], Uf[r2, j2], cfg.tau), INC)
        last = np.maximum((valid.sum(axis=1) - 1), 0)
        s2 = np.where(any2, times[j2], times[last])
        v[todo] = v2
        used = used.copy()
        used[todo] = used[todo] + s2
        settings[todo] = k + _settings_exact(case, s2.astype(float))
    return v, used, settings


def qv_dfe_rc(case: Case, cfg: OracleConfig, rng, R):
    """QV-DFE-RC: readout-corrected sequential DFE.

    Readout twirling (random X before measurement, classical bit flip after)
    makes each qubit's readout a symmetric flip with probability r_q, so the
    observed sign of a stabilizer g has mean c_g <g> with c_g = prod_{q in g}
    (1 - 2 r_q).  Dividing each shot by the calibrated c_g yields a bounded,
    unbiased estimator of the DFE mean; its empirical-Bernstein confidence
    sequence gives the fidelity bounds.  r_q is estimated per repetition from
    ``cal_shots`` twirled calibration shots (not counted in the budget).
    """
    if case.kind == "product":
        return _qv_product_rc(case, cfg, rng, R)
    m = case.m
    D = 2**m
    T = cfg.budget
    r_true = np.asarray(case.readout_sym, dtype=float)
    r_hat = rng.binomial(cfg.cal_shots, r_true, size=(R, m)) / cfg.cal_shots
    r_hat = np.minimum(r_hat, 0.45)
    log_att_true = np.log1p(-2 * r_true)                               # (m,)
    g = rng.integers(0, D - 1, size=(R, T))                           # sampled elements
    supp = case.elem_supp.astype(float)                                 # (D-1, m)
    c_true = np.exp(supp @ log_att_true)                                # (D-1,)
    mean_sign = c_true[g] * case.elem_exp[g]
    sign = np.where(rng.random((R, T)) < 0.5 * (1 + mean_sign), 1.0, -1.0)
    log_att_hat = np.log1p(-2 * r_hat)                                  # (R, m)
    c_hat_all = np.exp(log_att_hat @ supp.T)                            # (R, D-1)
    c_hat = np.take_along_axis(c_hat_all, g, axis=1)
    B = 1.0 / c_hat_all.min(axis=1, keepdims=True)                     # predictable bound
    Y = sign / c_hat
    Z = (Y + B) / (2 * B)
    lo, hi = eb_cs_path(Z, cfg.alpha)
    step = cfg.batch * 2
    idx = np.arange(step - 1, T, step)
    Fp_lo = 2 * B * lo[:, idx] - B
    Fp_hi = 2 * B * hi[:, idx] - B
    L = np.clip((Fp_lo * (D - 1) + 1) / D, 0, 1)
    U = np.clip((Fp_hi * (D - 1) + 1) / D, 0, 1)
    times = idx + 1
    v, shots = _stop(L, U, times, cfg.tau, times[-1])
    return v, shots, _settings_exact(case, shots)


def _qv_product_rc(case: Case, cfg: OracleConfig, rng, R):
    """Readout-corrected exact test for product targets.

    With twirled symmetric readout (flip probability r_q), the weight
    w_q(b) = A_q^{-1}[0, b] gives E[prod_q w_q(b'_q)] = P(all true bits are 0) = F
    exactly; the bounded per-shot estimator is covered by the PrPl-EB CS.
    """
    from .simulator import bit_table
    m = case.m
    T = cfg.budget
    r_true = np.asarray(case.readout_sym, dtype=float)
    r_hat = np.minimum(rng.binomial(cfg.cal_shots, r_true, size=(R, m)) / cfg.cal_shots, 0.45)
    idx = rng.choice(2**m, size=(R, T), p=case.product_dist / case.product_dist.sum())
    bits = bit_table(m)[idx]                                             # (R, T, m)
    flips = rng.random((R, T, m)) < r_true[None, None, :]
    meas = bits ^ flips
    w0 = (1 - r_hat) / (1 - 2 * r_hat)                                  # (R, m)
    w1 = -r_hat / (1 - 2 * r_hat)
    Y = np.prod(np.where(meas == 0, w0[:, None, :], w1[:, None, :]), axis=2)
    B = np.prod(w0, axis=1, keepdims=True)
    Z = (Y + B) / (2 * B)
    lo, hi = eb_cs_path(Z, cfg.alpha)
    step = cfg.batch * 2
    look = np.arange(step - 1, T, step)
    L = np.clip(2 * B * lo[:, look] - B, 0, 1)
    U = np.clip(2 * B * hi[:, look] - B, 0, 1)
    times = look + 1
    v, shots = _stop(L, U, times, cfg.tau, times[-1])
    return v, shots, np.ones(R)


ORACLES = {
    # label: (function, family)
    "Z-chi2": (z_chi2, "baseline"),
    "ZX-chi2": (zx_chi2, "baseline"),
    "Inverse-0tol": (inverse_zero_tol, "baseline"),
    "Pauli-tol": (pauli_tolerance, "baseline"),
    "Plugin-DFE": (plugin_exact, "baseline"),
    "CP-TG": (cp_cover, "fixed"),
    "CP-DFE": (cp_exact, "fixed"),
    "Peek-CP-TG": (peek_cp_cover, "invalid"),
    "QV-Z": (qv_z, "proposed"),
    "QV-TG": (qv_cover, "proposed"),
    "QV-DFE": (qv_exact, "proposed"),
    "QV-ESC": (qv_escalate, "proposed"),
    "QV-DFE-RC": (qv_dfe_rc, "proposed"),
}


def applicable(name: str, case: Case) -> bool:
    """Pauli-tol needs stabilizer test cases; every other oracle always applies."""
    return not (name == "Pauli-tol" and case.kind != "stabilizer")


def run_oracle(name: str, case: Case, cfg: OracleConfig, rng: np.random.Generator, R: int):
    fn, _ = ORACLES[name]
    v, s, k = fn(case, cfg, rng, R)
    return np.asarray(v, dtype=np.int8), np.asarray(s, dtype=float), np.asarray(k, dtype=float)
