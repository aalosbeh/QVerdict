"""Main benchmark (RQ1-RQ4): subjects x first-order mutants x noise x oracles.

Outputs
  results/cases.csv      one row per (subject, variant, noise): exact ground truth,
                         plan statistics and identified intervals (RQ1)
  results/benchmark.csv  one row per (case, oracle): verdict frequencies, shots,
                         settings and flip rate over R repetitions (RQ2-RQ4)
  results/benchmark_meta.json
"""
from __future__ import annotations

import argparse
import csv
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from common import (ALL_ORACLES, MUTANT_CAPS, NOISE, RESULTS, TAU, config, environment,
                    seed_for, summarize, write_json)
from qverdict.benchmark import default_suite
from qverdict.identify import lp_interval, union_interval
from qverdict.mutants import Mutant, sample_mutants
from qverdict.oracles import applicable, run_oracle
from qverdict.plans import cover_plan, exact_case, make_target, z_plan
from qverdict.simulator import density_matrix

_STATE: dict = {}


def build():
    suite = default_suite()
    items = []
    for si, s in enumerate(suite):
        variants = [Mutant("ORIG", "original", s.spec)]
        variants += sample_mutants(s.spec, MUTANT_CAPS, seed_for("mutants", s.name) % (2**32))
        tgt = make_target(s.spec, s.observed)
        items.append((s, tgt, cover_plan(tgt), z_plan(tgt), variants))
    return items


def _init():
    _STATE["items"] = build()


def work(task):
    si, vi, R, tau, oracles = task
    s, tgt, plan, zp, variants = _STATE["items"][si]
    var = variants[vi]
    cfg = config(tau=tau)
    case_rows, oracle_rows = [], []
    ideal_rho = density_matrix(var.circuit, NOISE["N0"])
    ideal_case = exact_case(var.circuit, s.spec, s.observed, tgt, plan, NOISE["N0"], rho_full=ideal_rho)
    z_tvd_ideal = 0.5 * float(np.abs(ideal_case.z_dist - ideal_case.z_expected).sum())
    for nk, nm in NOISE.items():
        rho = ideal_rho if nk == "N0" else density_matrix(var.circuit, nm)
        inv = density_matrix(var.circuit.compose(s.spec.inverse()), nm)
        case = exact_case(var.circuit, s.spec, s.observed, tgt, plan, nm, rho_full=rho, inverse_rho=inv)
        truth = bool(case.F >= tau - 1e-12)
        meta = dict(subject=s.name, family=s.family, contract=s.contract, target=tgt.kind, m=tgt.m,
                    k=plan.k, variant=vi, op=var.op, desc=var.desc, noise=nk,
                    F=case.F, F_ideal=ideal_case.F, truth=int(truth),
                    equivalent=int(ideal_case.F >= 1 - 1e-9))
        L_u, U_u = union_interval(case.cover_q, case.cover_q, case.cover_complete)
        if plan.atoms is not None:
            L_lp, U_lp = lp_interval(plan.atoms, case.cover_q, case.cover_q)
            Lz, Uz = lp_interval(zp.atoms, [case.z_q], [case.z_q])
        else:  # product target: the single product test is exact
            L_lp, U_lp = float(L_u), float(U_u)
            Lz, Uz = 0.0, 1.0
        case_rows.append(dict(**meta, q=";".join(f"{x:.6g}" for x in case.cover_q), z_q=case.z_q,
                              L_union=float(L_u), U_union=float(U_u), L_lp=L_lp, U_lp=U_lp,
                              L_z=Lz, U_z=Uz, z_tvd_ideal=z_tvd_ideal,
                              z_tvd=0.5 * float(np.abs(case.z_dist - case.z_expected).sum()),
                              exact_p=case.exact_p, inv_p0=case.inv_p0,
                              gates=len(var.circuit), twoq=var.circuit.two_qubit_count()))
        for name in oracles:
            if not applicable(name, case):
                continue
            rng = np.random.default_rng(seed_for("bench", s.name, vi, nk, name, tau))
            v, sh, k = run_oracle(name, case, cfg, rng, R)
            oracle_rows.append(dict(**meta, oracle=name, **summarize(v, sh, k, truth)))
    return case_rows, oracle_rows


def _write(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--quick", action="store_true", help="originals only (smoke test)")
    ap.add_argument("--tau", type=float, default=TAU)
    ap.add_argument("--oracles", default="all", help="comma-separated subset")
    args = ap.parse_args()
    oracles = ALL_ORACLES if args.oracles == "all" else args.oracles.split(",")
    t0 = time.perf_counter()
    items = build()
    tasks = [(si, vi, args.reps, args.tau, oracles) for si, it in enumerate(items)
             for vi in range(1 if args.quick else len(it[4]))]
    cases, orows = [], []
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init) as ex:
        for c, o in ex.map(work, tasks, chunksize=4):
            cases.extend(c)
            orows.extend(o)
    suffix = ("_quick" if args.quick else "") + ("" if args.tau == TAU else f"_tau{args.tau:g}")
    _write(RESULTS / f"cases{suffix}.csv", cases)
    _write(RESULTS / f"benchmark{suffix}.csv", orows)
    subjects = [{"name": s.name, "family": s.family, "contract": s.contract, "n": s.n,
                 "observed": len(s.observed), "target": t.kind, "settings": [x.setting for x in p.tests],
                 "gates": len(s.spec.mutable_indices()), "twoq": s.spec.two_qubit_count(),
                 "depth": s.spec.depth(), "variants": len(v), "description": s.description,
                 "mutants_by_op": {op: sum(1 for x in v if x.op == op) for op in ("QGD", "QGI", "QGR", "RGI")}}
                for s, t, p, _, v in items]
    write_json(f"benchmark_meta{suffix}.json", {
        "tau": args.tau, "oracles": oracles, "alpha": config().alpha, "budget": config().budget, "batch": config().batch,
        "esc_fraction": config().esc_fraction, "esc_warmup": config().esc_warmup, "prior": config().prior,
        "reps": args.reps, "noise": {k: v.__dict__ for k, v in NOISE.items()}, "mutant_caps": MUTANT_CAPS,
        "subjects": subjects, "n_cases": len(cases), "n_oracle_rows": len(orows),
        "environment": environment(), "elapsed_s": time.perf_counter() - t0})
    print(f"{len(cases)} cases, {len(orows)} oracle rows in {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
