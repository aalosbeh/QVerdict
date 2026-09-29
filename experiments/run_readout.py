"""RQ5(a): sensitivity to the trusted-measurement assumption.

Every benchmark variant under N1 gate noise is re-evaluated with symmetric,
independent readout bit flips of probability r on every measured qubit.  The
ground truth (fidelity of the prepared state) is unchanged; only the data the
oracles see are corrupted.
"""
from __future__ import annotations

import argparse
import csv
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from common import MUTANT_CAPS, NOISE, RESULTS, TAU, config, environment, seed_for, summarize, write_json
from qverdict.benchmark import default_suite
from qverdict.mutants import Mutant, sample_mutants
from qverdict.oracles import run_oracle
from qverdict.plans import cover_plan, exact_case, make_target
from qverdict.simulator import density_matrix

READOUT = [0.0, 0.005, 0.01, 0.02, 0.04]
ORACLES = ["Z-chi2", "Plugin-DFE", "CP-TG", "CP-DFE", "QV-TG", "QV-DFE", "QV-ESC", "QV-DFE-RC"]


def work(task):
    si, R = task
    s = default_suite()[si]
    tgt = make_target(s.spec, s.observed)
    plan = cover_plan(tgt)
    variants = [Mutant("ORIG", "original", s.spec)] + sample_mutants(
        s.spec, MUTANT_CAPS, seed_for("mutants", s.name) % (2**32))
    rows = []
    for vi, var in enumerate(variants):
        rho = density_matrix(var.circuit, NOISE["N1"])
        for r in READOUT:
            case = exact_case(var.circuit, s.spec, s.observed, tgt, plan, NOISE["N1"], readout=r, rho_full=rho)
            truth = bool(case.F >= TAU - 1e-12)
            for name in ORACLES:
                rng = np.random.default_rng(seed_for("readout", s.name, vi, r, name))
                v, sh, k = run_oracle(name, case, config(), rng, R)
                rows.append(dict(subject=s.name, variant=vi, op=var.op, readout=r, F=case.F,
                                 truth=int(truth), oracle=name, **summarize(v, sh, k, truth)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--workers", type=int, default=11)
    args = ap.parse_args()
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        rows = [r for rs in ex.map(work, [(i, args.reps) for i in range(len(default_suite()))]) for r in rs]
    with open(RESULTS / "readout.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    write_json("readout_meta.json", {"readout": READOUT, "reps": args.reps, "gate_noise": "N1",
                                     "environment": environment(), "elapsed_s": time.perf_counter() - t0})
    print(f"{len(rows)} rows in {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
