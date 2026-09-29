"""Confidence sets for a Bernoulli parameter.

* :func:`mixture_cs_table` -- time-uniform (anytime-valid) confidence sequence
  from the Beta-binomial mixture martingale (Robbins, 1970).  For every p the
  process ``M_t(p) = B(a+S_t, b+t-S_t) / (B(a,b) p^{S_t} (1-p)^{t-S_t})`` is a
  nonnegative martingale with ``M_0 = 1`` under i.i.d. Bernoulli(p) data, so by
  Ville's inequality ``P(exists t: M_t(p) >= 1/alpha) <= alpha``.  The set
  ``{p : M_t(p) < 1/alpha}`` therefore covers p simultaneously for all t.
* :func:`clopper_pearson_table` -- exact fixed-sample two-sided interval.

Tables are indexed by the success count ``S`` and cached per (t, alpha, prior).
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
from scipy.special import betaln
from scipy.stats import beta as beta_dist


def _log_mixture(p: np.ndarray, S: np.ndarray, t: int, a: float, b: float) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        ll = S * np.log(p) + (t - S) * np.log1p(-p)
    ll = np.where((S == 0) & (p == 0), 0.0, ll)
    ll = np.where((S == t) & (p == 1), 0.0, ll)
    return betaln(a + S, b + t - S) - betaln(a, b) - ll


@lru_cache(maxsize=32768)
def mixture_cs_table(t: int, alpha: float, a: float = 0.5, b: float = 0.5) -> tuple[np.ndarray, np.ndarray]:
    """Lower/upper limits of the mixture confidence sequence at time ``t``.

    Returns arrays ``lo, hi`` of length ``t+1``; entry ``S`` is the interval for
    ``S`` successes in ``t`` trials.  The interval is ``{p : log M_t(p) < log(1/alpha)}``,
    computed by vectorised bisection (60 iterations, error < 1e-18).
    """
    if t <= 0:
        return np.zeros(1), np.ones(1)
    S = np.arange(t + 1, dtype=float)
    c = np.log(1.0 / alpha)
    phat = S / t
    # lower limit: log M decreasing on [0, phat]
    lo_a, lo_b = np.zeros_like(S), phat.copy()
    hi_a, hi_b = phat.copy(), np.ones_like(S)
    for _ in range(60):
        mid = 0.5 * (lo_a + lo_b)
        inside = _log_mixture(mid, S, t, a, b) < c
        lo_b = np.where(inside, mid, lo_b)
        lo_a = np.where(inside, lo_a, mid)
        mid2 = 0.5 * (hi_a + hi_b)
        inside2 = _log_mixture(mid2, S, t, a, b) < c
        hi_a = np.where(inside2, mid2, hi_a)
        hi_b = np.where(inside2, hi_b, mid2)
    lo = np.where(_log_mixture(np.zeros_like(S), S, t, a, b) < c, 0.0, lo_a)
    hi = np.where(_log_mixture(np.ones_like(S), S, t, a, b) < c, 1.0, hi_b)
    return lo, hi


@lru_cache(maxsize=32768)
def clopper_pearson_table(n: int, alpha: float) -> tuple[np.ndarray, np.ndarray]:
    """Exact two-sided Clopper--Pearson limits for S = 0..n successes."""
    k = np.arange(n + 1)
    lo = np.zeros(n + 1)
    hi = np.ones(n + 1)
    lo[1:] = beta_dist.ppf(alpha / 2, k[1:], n - k[1:] + 1)
    hi[:-1] = beta_dist.ppf(1 - alpha / 2, k[:-1] + 1, n - k[:-1])
    return lo, hi


def mixture_cs_path(counts: np.ndarray, times: np.ndarray, alpha: float,
                    a: float = 0.5, b: float = 0.5, intersect: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Evaluate the confidence sequence along sampled paths.

    ``counts`` has shape (R, K): cumulative successes at the K checkpoint
    ``times``.  With ``intersect=True`` the running intersection is returned,
    which remains a valid confidence sequence and is monotone.
    """
    R, K = counts.shape
    lo = np.empty((R, K))
    hi = np.empty((R, K))
    for j, t in enumerate(times):
        tl, th = mixture_cs_table(int(t), float(alpha), a, b)
        lo[:, j] = tl[counts[:, j]]
        hi[:, j] = th[counts[:, j]]
    if intersect:
        lo = np.maximum.accumulate(lo, axis=1)
        hi = np.minimum.accumulate(hi, axis=1)
    return lo, hi


def eb_cs_path(X: np.ndarray, alpha: float, c: float = 0.5, intersect: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Predictable plug-in empirical-Bernstein confidence sequence (PrPl-EB).

    Waudby-Smith and Ramdas, JRSSB 86(1), 2024, Theorem 2 with the plug-in of
    their eq. (15).  ``X`` has shape (R, T) with entries in [0, 1] whose
    conditional mean is mu.  Returns lower/upper limits of shape (R, T) valid
    uniformly over t with probability >= 1 - alpha.
    """
    R, T = X.shape
    t = np.arange(1, T + 1, dtype=float)
    csum = np.cumsum(X, axis=1)
    mu_hat = (0.5 + csum) / (t + 1)                         # mu_hat_t, t = 1..T
    mu_prev = np.concatenate([np.full((R, 1), 0.5), mu_hat[:, :-1]], axis=1)
    sig2 = (0.25 + np.cumsum((X - mu_hat) ** 2, axis=1)) / (t + 1)
    sig2_prev = np.concatenate([np.full((R, 1), 0.25), sig2[:, :-1]], axis=1)
    lam = np.minimum(np.sqrt(2 * np.log(2 / alpha) / (sig2_prev * t * np.log1p(t))), c)
    v = 4 * (X - mu_prev) ** 2
    psi = (-np.log1p(-lam) - lam) / 4
    sl = np.cumsum(lam, axis=1)
    centre = np.cumsum(lam * X, axis=1) / sl
    radius = (np.log(2 / alpha) + np.cumsum(v * psi, axis=1)) / sl
    lo = np.clip(centre - radius, 0.0, 1.0)
    hi = np.clip(centre + radius, 0.0, 1.0)
    if intersect:
        lo = np.maximum.accumulate(lo, axis=1)
        hi = np.minimum.accumulate(hi, axis=1)
    return lo, hi
