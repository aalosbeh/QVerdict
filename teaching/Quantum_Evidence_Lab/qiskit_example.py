"""Local, account-free Qiskit cross-check and an executable teaching example."""
import json
from pathlib import Path
import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, DensityMatrix
from qiskit.primitives import StatevectorSampler
from experiment import cases, properties, H

def circuit(phase_error=False):
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0,1)
    if phase_error:
        qc.z(0)
    return qc

def main():
    example = {}
    sampler = StatevectorSampler(seed=20260924)
    for faulty in (False,True):
        name = "phase_flip" if faulty else "target"
        example[name] = {}
        for basis in ("Z","X"):
            qc = circuit(faulty)
            if basis == "X":
                qc.h(0); qc.h(1)
            exact = Statevector.from_instruction(qc).probabilities_dict()
            qc.measure_all()
            counts = sampler.run([qc],shots=256).result()[0].data.meas.get_counts()
            example[name][basis] = {"probabilities":{str(k):float(v) for k,v in exact.items()},"counts":counts}
    errors = []
    for name,rho,_ in cases():
        dm = DensityMatrix(rho)
        _,q = properties(rho)
        for basis in ("XX","YY","ZZ"):
            qc = QuantumCircuit(2)
            if basis == "XX":
                qc.h(0); qc.h(1)
            if basis == "YY":
                qc.sdg(0); qc.sdg(1); qc.h(0); qc.h(1)
            p = dm.evolve(qc).probabilities()
            failure = p[0]+p[3] if basis == "YY" else p[1]+p[2]
            errors.append(abs(float(failure)-q[basis]))
    assert max(errors) < 1e-12
    payload = {"qiskit":qiskit.__version__,"numpy":np.__version__,"cases_checked":len(cases()),"basis_checks":len(errors),"max_absolute_probability_error":max(errors),"example":example,"execution":"local ideal simulation only"}
    Path("results").mkdir(exist_ok=True)
    Path("results/qiskit_check.json").write_text(json.dumps(payload,indent=2))
    print(json.dumps(payload,indent=2))

if __name__ == "__main__":
    main()
