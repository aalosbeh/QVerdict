"""Cross-validate the NumPy simulator against Qiskit Aer (density-matrix method).

For every subject program and a seeded sample of mutants, the final density
matrix is computed by both simulators under the N2 noise model (depolarizing,
amplitude damping and dephasing after every non-ideal gate) and compared
entry-wise.  Requires the optional Qiskit environment (requirements-qiskit.txt).
"""
from __future__ import annotations

import time

import numpy as np

from common import NOISE, environment, seed_for, write_json
from qverdict.benchmark import default_suite
from qverdict.mutants import sample_mutants
from qverdict.simulator import _amp_damp_kraus, _dephase_kraus, density_matrix, gate_matrix

import qiskit
import qiskit_aer
from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate
from qiskit.quantum_info import DensityMatrix
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel as AerNoise, depolarizing_error, kraus_error


def to_qiskit(circ):
    qc = QuantumCircuit(circ.n)
    for i, (name, qubits, params) in enumerate(circ.gates):
        if i in circ.ideal:  # exempt from noise: opaque unitary not in the noise model
            U = gate_matrix(name, params)
            # UnitaryGate expects little-endian qubit order for multi-qubit gates
            if len(qubits) == 2:
                U = U.reshape(2, 2, 2, 2).transpose(1, 0, 3, 2).reshape(4, 4)
            qc.append(UnitaryGate(U), list(qubits))
            continue
        if name == "cp":
            qc.cp(params[0], *qubits)
        elif name in ("rx", "ry", "rz", "p"):
            getattr(qc, name)(params[0], *qubits)
        elif name == "id":
            qc.id(*qubits)
        else:
            getattr(qc, name)(*qubits)
    qc.save_density_matrix()
    return qc


def aer_noise(nm):
    model = AerNoise(basis_gates=["h", "x", "y", "z", "s", "sdg", "t", "tdg", "rx", "ry", "rz", "p",
                                  "cx", "cz", "swap", "cp", "id", "unitary"])
    local = kraus_error(_amp_damp_kraus(nm.gamma)).compose(kraus_error(_dephase_kraus(nm.lam)))
    e1 = depolarizing_error(nm.p1, 1).compose(local)
    e2 = depolarizing_error(nm.p2, 2).compose(local.tensor(local))
    model.add_all_qubit_quantum_error(e1, ["h", "x", "y", "z", "s", "sdg", "t", "tdg", "rx", "ry", "rz", "p", "id"])
    model.add_all_qubit_quantum_error(e2, ["cx", "cz", "swap", "cp"])
    return model


def main():
    t0 = time.perf_counter()
    nm = NOISE["N2"]
    sim = AerSimulator(method="density_matrix", noise_model=aer_noise(nm))
    rows = []
    for s in default_suite():
        variants = [s.spec] + [m.circuit for m in
                               sample_mutants(s.spec, {"QGD": 2, "QGI": 3, "QGR": 2, "RGI": 3}, seed_for("xval", s.name))]
        for k, circ in enumerate(variants):
            ours = density_matrix(circ, nm)
            qc = to_qiskit(circ)
            res = sim.run(qc, shots=1).result()
            aer = DensityMatrix(res.data()["density_matrix"]).reverse_qargs().data
            rows.append({"subject": s.name, "variant": k, "n": circ.n,
                         "max_abs_diff": float(np.max(np.abs(ours - aer)))})
    worst = max(r["max_abs_diff"] for r in rows)
    payload = {"noise": nm.__dict__, "comparisons": len(rows), "max_abs_diff": worst,
               "qiskit": qiskit.__version__, "qiskit_aer": qiskit_aer.__version__,
               "environment": environment(), "elapsed_s": time.perf_counter() - t0, "rows": rows}
    write_json("crossval_qiskit.json", payload)
    print(f"{len(rows)} density matrices compared; max |difference| = {worst:.3e}")
    assert worst < 1e-10, "simulator disagreement"


if __name__ == "__main__":
    main()
