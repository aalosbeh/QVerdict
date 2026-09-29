"""RQ2: operating characteristics near the contract threshold.

For five subjects and two fault families whose fidelity is controlled exactly,
we sweep the true fidelity F across tau and estimate P(PASS), P(FAIL),
P(INCONCLUSIVE) and the wrong-verdict rate of every oracle with R repetitions.

  coherent   : an Rz(theta) over-rotation on qubit 0, F = cos^2(theta/2)
  incoherent : global depolarizing of the output, F = 1 - lambda (1 - 1/D)
"""
from __future__ import annotations

import argparse
import csv
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from common import ALL_ORACLES, RESULTS, TAU, config, environment, seed_for, summarize, write_json
from qverdict.benchmark import bell, cluster, ghz, qft, steane_zero
from qverdict.oracles import applicable, run_oracle
from qverdict.plans import cover_plan, exact_case, make_target
from qverdict.simulator import density_matrix

F_GRID = [0.80, 0.84, 0.86, 0.88, 0.89, 0.895, 0.90, 0.905, 0.91, 0.92, 0.94, 0.96, 0.98, 1.00]
SUBJECTS = {"Bell": bell, "GHZ-4": lambda: ghz(4), "Cluster-6": lambda: cluster(6),
            "Steane-7": steane_zero, "QFT-4": lambda: qft(4, 0b1011)}


def work(task):
    sname, family, Ft, R = task
    s = SUBJECTS[sname]()
    tgt = make_target(s.spec, s.observed)
    plan = cover_plan(tgt)
    D = 2**tgt.m
    if family == "coherent":
        theta = 2 * np.arccos(np.sqrt(Ft))
        prog = s.spec.copy().add("rz", 0, params=[theta])
        rho = density_matrix(prog)
    else:
        lam = (1 - Ft) / (1 - 1 / D)
        psi = tgt.psi
        rho = (1 - lam) * np.outer(psi, psi.conj()) + lam * np.eye(D) / D
        prog = s.spec
    inv = density_matrix(s.spec.inverse(), rho0=rho)
    case = exact_case(prog, s.spec, s.observed, tgt, plan, rho_full=rho, inverse_rho=inv)
    assert abs(case.F - Ft) < 1e-9, (sname, family, Ft, case.F)
    truth = bool(case.F >= TAU - 1e-12)
    rows = []
    for name in ALL_ORACLES:
        if not applicable(name, case):
            continue
        rng = np.random.default_rng(seed_for("boundary", sname, family, Ft, name))
        v, sh, k = run_oracle(name, case, config(), rng, R)
        rows.append(dict(subject=sname, family=family, F=Ft, truth=int(truth), oracle=name,
                         **summarize(v, sh, k, truth)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=14)
    args = ap.parse_args()
    t0 = time.perf_counter()
    tasks = [(s, fam, F, args.reps) for s in SUBJECTS for fam in ("coherent", "incoherent") for F in F_GRID]
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for r in ex.map(work, tasks):
            rows.extend(r)
    with open(RESULTS / "boundary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    write_json("boundary_meta.json", {"F_grid": F_GRID, "subjects": list(SUBJECTS), "reps": args.reps,
                                      "tau": TAU, "environment": environment(),
                                      "elapsed_s": time.perf_counter() - t0})
    print(f"{len(rows)} rows in {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
