"""Bell-state evidence laboratory. Simulated data only; no student data.

Python 3.10+, NumPy and SciPy. Run: python experiment.py --out results
This demonstrates established state-verification ideas, not a new verifier.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import platform
import time
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import beta

ALPHA = 0.05
THRESHOLD = 0.90
BUDGETS = (96, 384, 1536)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
PHI = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
TARGET = np.outer(PHI, PHI.conj())
OBS = {"XX": np.kron(X, X), "YY": np.kron(Y, Y), "ZZ": np.kron(Z, Z)}

def pure(v):
    v = np.asarray(v, dtype=complex)
    v = v / np.linalg.norm(v)
    return np.outer(v, v.conj())

def cases():
    """Hand-selected teaching fixtures, not a representative defect dataset."""
    pm = pure([1, 0, 0, -1])
    items = [
        ("target", TARGET, "reference"),
        ("global_phase", pure(np.exp(0.7j) * PHI), "equivalent control"),
        ("phase_flip", pm, "semantic mismatch"),
        ("bit_flip", pure([0, 1, 1, 0]), "semantic mismatch"),
        ("missing_entangler", pure([1, 1, 0, 0]), "semantic mismatch"),
        ("zero_state", pure([1, 0, 0, 0]), "semantic mismatch"),
        ("plus_plus", pure([1, 1, 1, 1]), "semantic mismatch"),
        ("dephased", np.diag([0.5, 0, 0, 0.5]), "incoherent mixture"),
        ("phase_rotation_0_6", pure([1, 0, 0, np.exp(0.6j)]), "near threshold"),
        ("phase_rotation_0_7", pure([1, 0, 0, np.exp(0.7j)]), "near threshold"),
    ]
    for p in (0.03, 0.08, 0.10, 0.12, 0.20):
        items.append((f"phase_mixture_{p:.2f}", (1-p)*TARGET + p*pm, "known phase mixture"))
    for p in (0.08, 0.20):
        items.append((f"depolarized_{p:.2f}", (1-p)*TARGET + p*np.eye(4)/4, "known depolarizing mixture"))
    return items

def properties(rho):
    fidelity = float(np.trace(rho @ TARGET).real)
    q = {}
    for basis, operator in OBS.items():
        expected_sign = -1 if basis == "YY" else 1
        q[basis] = float(np.clip((1-expected_sign*np.trace(rho @ operator).real)/2, 0, 1))
    return fidelity, q

def cp_table(n, failure_probability):
    """Two-sided exact Clopper-Pearson intervals at a prespecified look."""
    k = np.arange(n+1)
    tail = failure_probability / 2
    lo = np.zeros(n+1)
    hi = np.ones(n+1)
    lo[1:] = beta.ppf(tail, k[1:], n-k[1:]+1)
    hi[:-1] = beta.ppf(1-tail, k[:-1]+1, n-k[:-1])
    return lo, hi

def fidelity_bounds(intervals):
    if "YY" in intervals:
        lower = 1 - sum(v[1] for v in intervals.values()) / 2
        upper = 1 - sum(v[0] for v in intervals.values()) / 2
    else:
        lower = 1 - sum(v[1] for v in intervals.values())
        upper = 1 - max(v[0] for v in intervals.values())
    return max(0.0, lower), min(1.0, upper)

def verdict(lower, upper):
    if lower >= THRESHOLD:
        return "supported"
    if upper < THRESHOLD:
        return "contradicted"
    return "inconclusive"

def self_check():
    f, q = properties(TARGET)
    assert np.isclose(f, 1) and all(np.isclose(v, 0) for v in q.values())
    _, qminus = properties(pure([1, 0, 0, -1]))
    assert np.isclose(qminus["ZZ"], 0) and np.isclose(qminus["XX"], 1)
    rng = np.random.default_rng(93)
    for _ in range(200):
        a = rng.normal(size=(4,4)) + 1j*rng.normal(size=(4,4))
        rho = a @ a.conj().T
        rho /= np.trace(rho)
        f, q = properties(rho)
        lo, hi = fidelity_bounds({b:(q[b],q[b]) for b in ("XX","ZZ")})
        assert lo - 1e-12 <= f <= hi + 1e-12
        assert np.isclose(f, 1-sum(q.values())/2)
    for n in (1,48,192,768):
        lo, hi = cp_table(n, ALPHA/6)
        assert lo[0] == 0 and hi[-1] == 1
        assert np.all(lo <= hi)
    return "Analytic Bell fixtures and 200 random density matrices passed."

def run(out, repetitions=400, seed=20260924):
    start = time.perf_counter()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    checks = self_check()
    methods = ("z_only_teaching_negative_control", "fixed_XX_ZZ", "staged_XX_ZZ", "fixed_XX_YY_ZZ")
    tables = {}
    for n in [b//2 for b in BUDGETS]:
        tables[(n,6)] = cp_table(n, ALPHA/6)
    tables[(BUDGETS[-1]//2,2)] = cp_table(BUDGETS[-1]//2, ALPHA/2)
    tables[(BUDGETS[-1]//3,3)] = cp_table(BUDGETS[-1]//3, ALPHA/3)
    rows, observations, catalog = [], [], []
    for index, (name, rho, kind) in enumerate(cases()):
        fidelity, q = properties(rho)
        truth = fidelity >= THRESHOLD - 1e-12
        catalog.append({"case":name,"kind":kind,"fidelity":fidelity,"meets_contract":truth,"q":q})
        for rep in range(repetitions):
            rng = np.random.default_rng(np.random.SeedSequence([seed,index,rep]))
            # Share basis-specific samples across strategies for a paired comparison.
            cumulative = {b:np.cumsum(rng.random(BUDGETS[-1]) < q[b]) for b in OBS}
            for method in methods:
                looks = BUDGETS if method == "staged_XX_ZZ" else (BUDGETS[-1],)
                for budget in looks:
                    bases = ("ZZ",) if method.startswith("z_only") else (("XX","YY","ZZ") if "YY" in method else ("XX","ZZ"))
                    n = budget // len(bases)
                    counts = {b:int(cumulative[b][n-1]) for b in bases}
                    if method.startswith("z_only"):
                        # Deliberately inadequate student heuristic; not a serious state-verification baseline.
                        decision = "supported" if counts["ZZ"]/n <= 1-THRESHOLD else "contradicted"
                        lower, upper = None, None
                    else:
                        multiplicity = 6 if method.startswith("staged") else len(bases)
                        lo, hi = tables[(n,multiplicity)]
                        intervals = {b:(float(lo[counts[b]]),float(hi[counts[b]])) for b in bases}
                        lower, upper = fidelity_bounds(intervals)
                        decision = verdict(lower,upper)
                    obs = {"case":name,"repeat":rep,"method":method,"shots":budget,"n_per_basis":n,"k_XX":counts.get("XX"),"k_YY":counts.get("YY"),"k_ZZ":counts.get("ZZ"),"fidelity_lower":lower,"fidelity_upper":upper,"decision":decision}
                    observations.append(obs)
                    if decision != "inconclusive":
                        break
                wrong = (decision == "supported" and not truth) or (decision == "contradicted" and truth)
                rows.append({**obs,"true_fidelity":fidelity,"meets_contract":truth,"wrong_decision":wrong})
    for fname, data in (("trials.csv",rows),("observations.csv",observations)):
        with (out/fname).open("w",newline="") as f:
            writer = csv.DictWriter(f,fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    summary = []
    for name,_,_ in cases():
        for method in methods:
            subset = [r for r in rows if r["case"] == name and r["method"] == method]
            summary.append({"case":name,"method":method,"repetitions":repetitions,"supported":sum(r["decision"] == "supported" for r in subset),"contradicted":sum(r["decision"] == "contradicted" for r in subset),"inconclusive":sum(r["decision"] == "inconclusive" for r in subset),"wrong_decisions":sum(r["wrong_decision"] for r in subset),"mean_shots":float(np.mean([r["shots"] for r in subset]))})
    with (out/"summary.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    overall = {}
    for method in methods:
        subset = [r for r in rows if r["method"] == method]
        overall[method] = {"n":len(subset),"wrong_decisions":sum(r["wrong_decision"] for r in subset),"inconclusive":sum(r["decision"] == "inconclusive" for r in subset),"mean_shots":float(np.mean([r["shots"] for r in subset]))}
    payload = {"data_type":"synthetic measurement samples from specified density matrices; no human participants or QPU runs", "seed":seed,"repetitions_per_case":repetitions,"cases":len(catalog),"alpha_per_case_run":ALPHA,"fidelity_threshold":THRESHOLD,"budgets":BUDGETS,"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,"self_check":checks,"elapsed_seconds":round(time.perf_counter()-start,3),"experiment_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"overall":overall,"catalog":catalog}
    (out/"results.json").write_text(json.dumps(payload,indent=2))
    print(json.dumps({k:v for k,v in payload.items() if k != "catalog"},indent=2))
    return payload

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out",default="results")
    parser.add_argument("--repetitions",type=int,default=400)
    parser.add_argument("--seed",type=int,default=20260924)
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("repetitions must be positive")
    run(args.out,args.repetitions,args.seed)
