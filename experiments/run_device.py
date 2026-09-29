"""RQ5(b): device-calibrated noise from IBM backend snapshots (Qiskit fake backends).

Each state-contract subject (original + seeded mutants) is transpiled to the
backend (optimisation level 3, noise-aware layout, fixed seed), simulated with Aer's
density-matrix method under the backend's calibrated noise model (gate errors,
thermal relaxation), and evaluated by the oracles with and without the
backend's calibrated, asymmetric readout errors.  Ground truth is the
fidelity of the simulated pre-measurement state.
Requires requirements-qiskit.txt.
"""
from __future__ import annotations

import argparse
import csv
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from common import MUTANT_CAPS, RESULTS, TAU, config, environment, seed_for, summarize, write_json
from qverdict.benchmark import default_suite
from qverdict.mutants import Mutant, sample_mutants
from qverdict.oracles import applicable, run_oracle
from qverdict.plans import cover_plan, exact_case, make_target

DEVICES = ["FakeTorino", "FakeSherbrooke"]
SUBJECTS = ["Bell", "GHZ-4", "GHZ-8", "Cluster-6", "Ring-5", "Steane-7", "BV-5", "QFT-4"]
ORACLES = ["Z-chi2", "ZX-chi2", "Inverse-0tol", "Pauli-tol", "Plugin-DFE", "CP-TG", "CP-DFE",
           "QV-TG", "QV-DFE", "QV-ESC", "QV-DFE-RC"]
N_MUTANTS = 24


def _qc(circ):
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(circ.n)
    for name, qubits, params in circ.gates:
        if name == "cp":
            qc.cp(params[0], *qubits)
        elif name in ("rx", "ry", "rz", "p"):
            getattr(qc, name)(params[0], *qubits)
        else:
            getattr(qc, name)(*qubits)
    return qc


def _simulate(qc, backend, sim, keep):
    """Density matrix of logical qubits ``keep`` after transpilation (big-endian)."""
    from qiskit import transpile
    from qiskit.quantum_info import DensityMatrix
    tqc = transpile(qc, backend=backend, optimization_level=3, seed_transpiler=7)
    final = tqc.layout.final_index_layout()
    phys = [final[q] for q in keep]
    tqc.save_density_matrix(qubits=phys)
    res = sim.run(tqc, shots=1).result()
    dm = DensityMatrix(res.data()["density_matrix"]).reverse_qargs().data
    twoq = sum(1 for inst in tqc.data if inst.operation.num_qubits == 2)
    return dm, phys, twoq


def work(task):
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel
    import qiskit_ibm_runtime.fake_provider as fp
    dev, sname, R = task
    backend = getattr(fp, dev)()
    nm = NoiseModel.from_backend(backend)
    sim = AerSimulator(method="density_matrix", noise_model=nm)
    s = next(x for x in default_suite() if x.name == sname)
    tgt = make_target(s.spec, s.observed)
    plan = cover_plan(tgt)
    muts = sample_mutants(s.spec, MUTANT_CAPS, seed_for("mutants", s.name) % (2**32))
    rng0 = np.random.default_rng(seed_for("device-pick", sname))
    pick = sorted(rng0.choice(len(muts), size=min(N_MUTANTS, len(muts)), replace=False))
    variants = [Mutant("ORIG", "original", s.spec)] + [muts[i] for i in pick]
    rows = []
    for vi, var in enumerate(variants):
        rho, phys, twoq = _simulate(_qc(var.circuit), backend, sim, s.observed)
        inv_qc = _qc(var.circuit)
        inv_qc.barrier()  # keep the transpiler from cancelling program and uncompute
        inv_qc.compose(_qc(s.spec.inverse()), inplace=True)
        inv_dm, inv_phys, _ = _simulate(inv_qc, backend, sim, list(range(s.n)))
        ro = nm._local_readout_errors  # {(q,): ReadoutError}
        flips = [(float(ro[(q,)].probabilities[0][1]), float(ro[(q,)].probabilities[1][0])) for q in phys]
        inv_flips = [(float(ro[(q,)].probabilities[0][1]), float(ro[(q,)].probabilities[1][0])) for q in inv_phys]
        for with_ro in (False, True):
            case = exact_case(var.circuit, s.spec, list(range(len(s.observed))), tgt, plan,
                              readout=flips if with_ro else None, rho_full=rho,
                              inverse_rho=None)
            # inverse test: P(all zeros) with the uncompute circuit on device
            from qverdict.simulator import apply_readout
            p_inv = np.real(np.diag(inv_dm)).clip(0)
            p_inv = apply_readout(p_inv / p_inv.sum(), inv_flips if with_ro else [(0.0, 0.0)] * s.n)
            case.inv_p0 = float(p_inv[0])
            truth = bool(case.F >= TAU - 1e-12)
            for name in ORACLES:
                if not applicable(name, case):
                    continue
                rng = np.random.default_rng(seed_for("device", dev, sname, vi, with_ro, name))
                v, sh, k = run_oracle(name, case, config(), rng, R)
                rows.append(dict(device=dev, subject=sname, variant=vi, op=var.op, readout=int(with_ro),
                                 F=case.F, truth=int(truth), twoq_transpiled=twoq,
                                 mean_readout_err=float(np.mean([0.5 * (a + b) for a, b in flips])),
                                 oracle=name, **summarize(v, sh, k, truth)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--workers", type=int, default=14)
    args = ap.parse_args()
    t0 = time.perf_counter()
    tasks = [(d, s, args.reps) for d in DEVICES for s in SUBJECTS]
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        rows = [r for rs in ex.map(work, tasks) for r in rs]
    with open(RESULTS / "device.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    import qiskit, qiskit_aer, qiskit_ibm_runtime
    write_json("device_meta.json", {"devices": DEVICES, "subjects": SUBJECTS, "mutants_per_subject": N_MUTANTS,
                                    "reps": args.reps, "qiskit": qiskit.__version__,
                                    "qiskit_aer": qiskit_aer.__version__,
                                    "qiskit_ibm_runtime": qiskit_ibm_runtime.__version__,
                                    "transpile": {"optimization_level": 3, "seed_transpiler": 7},
                                    "environment": environment(), "elapsed_s": time.perf_counter() - t0})
    print(f"{len(rows)} rows in {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
