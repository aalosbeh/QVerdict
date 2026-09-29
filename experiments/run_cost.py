"""RQ3: cost and resolution.

(a) Budget sweep: all originals and RGI (coherent over-rotation) mutants under
    N1 and N2, budgets 512..32768, certified oracles only.
(b) Width scaling: GHZ-n and linear cluster-n, n = 2..10, under N1.
"""
from __future__ import annotations

import argparse
import csv
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from common import MUTANT_CAPS, NOISE, RESULTS, TAU, config, environment, seed_for, summarize, write_json
from qverdict.benchmark import cluster, default_suite, ghz
from qverdict.mutants import Mutant, sample_mutants
from qverdict.oracles import run_oracle
from qverdict.plans import cover_plan, exact_case, make_target
from qverdict.simulator import density_matrix

BUDGETS = [512, 1024, 2048, 4096, 8192, 16384, 32768]
CERTIFIED = ["CP-TG", "CP-DFE", "QV-TG", "QV-DFE", "QV-ESC"]
SEQUENTIAL = ["QV-TG", "QV-DFE", "QV-ESC"]


def budget_task(task):
    si, R = task
    s = default_suite()[si]
    tgt = make_target(s.spec, s.observed)
    plan = cover_plan(tgt)
    variants = [Mutant("ORIG", "original", s.spec)] + [
        m for m in sample_mutants(s.spec, MUTANT_CAPS, seed_for("mutants", s.name) % (2**32)) if m.op == "RGI"]
    rows = []
    for vi, var in enumerate(variants):
        for nk in ("N1", "N2"):
            case = exact_case(var.circuit, s.spec, s.observed, tgt, plan, NOISE[nk])
            truth = bool(case.F >= TAU - 1e-12)
            for B in BUDGETS:
                for name in CERTIFIED:
                    rng = np.random.default_rng(seed_for("budget", s.name, vi, nk, B, name))
                    v, sh, k = run_oracle(name, case, config(budget=B), rng, R)
                    rows.append(dict(subject=s.name, variant=vi, op=var.op, noise=nk, F=case.F,
                                     truth=int(truth), budget=B, oracle=name, **summarize(v, sh, k, truth)))
    return rows


def scaling_task(task):
    fam, n, R = task
    s = ghz(n) if fam == "GHZ" else cluster(n)
    tgt = make_target(s.spec, s.observed)
    plan = cover_plan(tgt)
    rho = density_matrix(s.spec, NOISE["N1"])
    case = exact_case(s.spec, s.spec, s.observed, tgt, plan, NOISE["N1"], rho_full=rho)
    truth = bool(case.F >= TAU - 1e-12)
    rows = []
    for name in SEQUENTIAL + ["CP-TG", "CP-DFE"]:
        rng = np.random.default_rng(seed_for("scaling", fam, n, name))
        v, sh, k = run_oracle(name, case, config(budget=32768), rng, R)
        rows.append(dict(family=fam, n=n, F=case.F, L_union=float(max(0, 1 - case.cover_q.sum())),
                         truth=int(truth), oracle=name, **summarize(v, sh, k, truth)))
    return rows


def _write(name, rows):
    with open(RESULTS / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--workers", type=int, default=14)
    args = ap.parse_args()
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        brows = [r for rs in ex.map(budget_task, [(i, args.reps) for i in range(len(default_suite()))]) for r in rs]
        srows = [r for rs in ex.map(scaling_task, [(f, n, 500) for f in ("GHZ", "Cluster") for n in range(2, 11)])
                 for r in rs]
    _write("budget.csv", brows)
    _write("scaling.csv", srows)
    write_json("cost_meta.json", {"budgets": BUDGETS, "reps": args.reps, "scaling_reps": 500,
                                  "scaling_budget": 32768, "environment": environment(),
                                  "elapsed_s": time.perf_counter() - t0})
    print(f"budget rows {len(brows)}, scaling rows {len(srows)} in {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
