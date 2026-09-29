# QVerdict: sound, anytime-valid test oracles for quantum programs

**QVerdict** decides whether a quantum program meets a *fidelity contract*: "the output
state of these qubits has fidelity at least τ with the intended state." Instead of a binary
pass/fail computed from a fixed number of computational-basis shots, it returns

| Verdict | Meaning |
|---|---|
| `PASS` | the evidence certifies `F ≥ τ` |
| `FAIL` | the evidence certifies `F < τ` |
| `INCONCLUSIVE` | the evidence does not yet decide the contract |

and guarantees that a `PASS` or `FAIL` is wrong with probability at most α. The guarantee
holds for **every** program and noise process that acts identically on each execution, **every**
stopping time (you may watch the results and stop whenever you like), and **every** adaptive
choice of measurement settings.

This repository accompanies the paper *"Pass, Fail, or Not Yet: Sound and Anytime-Valid Test
Oracles for Quantum Programs"* (see [`paper/`](paper/)). It contains the library, the complete
empirical study, all raw results, and scripts that regenerate every table, figure and number
in the paper.

## Why?

A relative-phase fault turns the Bell state `(|00⟩+|11⟩)/√2` into `(|00⟩−|11⟩)/√2`. Both give
identical computational-basis statistics, so a χ² oracle accepts the faulty program as often as
the correct one. The paper proves that this is unavoidable: **no sound oracle that sees only
computational-basis data can accept a program whose target has no dominant basis amplitude**,
including a correct one. On noisy devices, binary oracles also flip between runs near the
tolerance, and fixed-sample confidence intervals become invalid as soon as you stop early.

QVerdict solves all three problems:

1. **Observability analysis.** It compiles a Clifford or product-state specification into
   local measurement plans and computes *before testing* which fidelities each plan can
   distinguish, via an exact linear program (Theorem 1). This separates structural ambiguity,
   which more shots cannot fix, from statistical ambiguity.
2. **Anytime-valid verdicts.** It turns stabilizer fidelity bounds and confidence sequences
   into three-valued verdicts that stop as soon as the evidence is decisive (Theorem 2).
3. **Readout robustness.** Twirled, calibrated readout correction keeps verdicts sound
   under measurement errors (Proposition 2).

## Headline results (from `results/`, reproduced by one command)

- Computational-basis χ² oracles gave wrong verdicts in about 32% of runs. They accepted
  phase-invisible faults in most runs.
- The proposed oracles kept **every** program's wrong-verdict rate below α = 5%, including
  at the tolerance boundary. The plug-in estimator reached 52% wrong there, and
  "peeking" Clopper–Pearson reached 22%.
- QV-DFE needed about 12× fewer shots than a fixed budget of 8192.
- Under IBM device-calibrated readout errors, every uncorrected oracle produced false
  failures; the readout-corrected QV-DFE-RC stayed below α.

Exact figures are in `paper/generated/numbers.tex` after running the study.

## Installation

Python ≥ 3.10. The core library needs only NumPy and SciPy (Matplotlib for figures).

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # pinned versions used for the paper
pip install -e .                   # installs the qverdict package
```

Optional Qiskit/Aer components (cross-validation and device-calibrated noise):

```bash
pip install -r requirements-qiskit.txt
```

## Quick start

```python
import numpy as np
from qverdict import Circuit, NoiseModel, make_target, cover_plan, exact_case
from qverdict import OracleConfig, run_oracle, PASS, FAIL, INC

spec = Circuit(2).add("h", 0).add("cx", 0, 1)      # specification: Bell state |Phi+>
buggy = spec.copy().add("z", 0)                    # phase fault: prepares |Phi->
target = make_target(spec, observed=[0, 1])        # stabilizer target {XX, -YY, ZZ}
plan = cover_plan(target)                          # two settings: ZZ and XX
cfg = OracleConfig(budget=8192, alpha=0.05, tau=0.90)
rng = np.random.default_rng(0)

scenarios = {
    "phase fault, no noise": (buggy, NoiseModel()),
    "correct program, noisy": (spec, NoiseModel(p1=1e-3, p2=1e-2)),
}
for label, (program, noise) in scenarios.items():
    case = exact_case(program, spec, [0, 1], target, plan, noise)
    print(f"{label}: true fidelity {case.F:.3f}")
    for name in ("Z-chi2", "QV-TG", "QV-DFE", "QV-ESC"):
        v, shots, _ = run_oracle(name, case, cfg, rng, R=200)
        print(f"  {name:7s} PASS {np.mean(v == PASS):.2f}  FAIL {np.mean(v == FAIL):.2f}"
              f"  INC {np.mean(v == INC):.2f}  mean shots {shots.mean():.0f}")
```

Without noise, `Z-chi2` passes the phase fault in about 95% (that is, 1 − α) of runs, because the fault is
invisible in the computational basis. With realistic noise, it fails the *correct* program,
because noise produces outputs that the ideal circuit never does. The QVerdict oracles fail
the fault within a few dozen shots and pass the noisy correct program, whose fidelity
exceeds τ.

`exact_case` computes exact outcome probabilities from a simulated density matrix, which
is how the study obtains ground truth. To test a real device, feed measured outcomes of the
plan's settings into `qverdict.confseq` and `qverdict.identify` in the same way as
`qverdict.oracles`.

## Reproducing the paper

```bash
cd experiments
./run_all.sh          # ~20 minutes on a 16-core laptop; set PYTHON=/path/to/python if needed
```

This runs the tests and all experiments, writes `results/*.csv|json`, and regenerates
`paper/figures/*.pdf` and `paper/generated/*.tex`. Individual steps:

| Script | Paper element |
|---|---|
| `experiments/run_benchmark.py` | RQ1–RQ4, Tables 2–4 and 6 (11 programs, 1102 mutants, 3 noise models, 1000 runs/case) |
| `experiments/run_benchmark.py --tau 0.8/0.95` | threshold sensitivity, Table 5 |
| `experiments/run_boundary.py` | RQ2 boundary sweep, Fig. 5 |
| `experiments/run_cost.py` | RQ3 budget sweep and width scaling, Figs. 6–7 |
| `experiments/run_readout.py` | RQ5 readout sweep, Fig. 8a |
| `experiments/run_device.py` | RQ5 IBM device-calibrated noise, Table 7, Fig. 8b (needs Qiskit) |
| `experiments/crossval_qiskit.py` | simulator vs. Qiskit Aer cross-check (needs Qiskit) |
| `scripts/make_figures.py`, `scripts/make_tables.py` | all figures, tables and numeric macros |

Randomness is fully seeded (SHA-256 of case identifiers). Different library versions can
change individual random draws but not the conclusions.

## Repository layout

```
src/qverdict/
  pauli.py        Pauli algebra, Clifford conjugation, stabilizer groups
  circuits.py     gate-list circuits (ideal gates for Choi constructions)
  simulator.py    exact state-vector / density-matrix simulation, noise, readout
  plans.py        targets, cover/exact plans, exact case statistics
  identify.py     identified-interval LP (Theorem 1) and closed-form bounds
  confseq.py      Beta-binomial mixture and empirical-Bernstein confidence sequences
  oracles.py      proposed oracles and all baselines
  benchmark.py    the 11 subject programs
  mutants.py      QGD / QGI / QGR / RGI mutation operators
experiments/      one script per research question + run_all.sh
scripts/          analysis, figures, tables
tests/            68 unit and statistical tests (pytest)
results/          raw outputs used in the paper
paper/            LaTeX source (IEEEtran), figures, generated tables, references,
                  submission checklist and cover-letter draft
teaching/         the original Bell-state evidence lab and handout (separate environment)
```

## Oracles implemented

| Name | Kind | Description |
|---|---|---|
| `Z-chi2` | baseline | unexpected-output check + Pearson χ² in the computational basis |
| `ZX-chi2` | baseline | the same in Z and in the all-Hadamard basis |
| `Pauli-tol` | baseline | stabilizer expectations within a fixed 1% tolerance (QOPS-style) |
| `Inverse-0tol` | baseline | program + inverse specification, fail on any nonzero outcome |
| `Plugin-DFE` | baseline | point estimate of fidelity vs. τ (no uncertainty) |
| `CP-TG`, `CP-DFE` | fixed-N certified | Clopper–Pearson + Bonferroni, three-valued |
| `Peek-CP-TG` | invalid ablation | CP intervals checked after every batch |
| `QV-Z` | proposed (control) | sound oracle restricted to Z-basis data (can only fail) |
| `QV-TG` | proposed | anytime-valid, cover (two-setting) plan |
| `QV-DFE` | proposed | anytime-valid, direct fidelity estimation / product test |
| `QV-ESC` | proposed | cover plan first, escalate to DFE on ambiguity |
| `QV-DFE-RC` | proposed | readout-twirled and corrected DFE (empirical-Bernstein CS) |

## Testing

```bash
pytest -q        # 68 tests, about 10 s
```

## Scope and limitations

- Guarantees assume that the executions are independent and prepare identical states, and
  that readout is trusted or twirled and calibrated (QV-DFE-RC).
- Cover plans need a stabilizer target. Exact plans need a stabilizer or product target.
  Other targets need importance-sampled DFE or a trusted inverse circuit (future work).
- The prototype enumerates stabilizer groups explicitly and targets registers of up to
  about 12 qubits.
- All reported experiments are simulations, including the device-calibrated ones. No quantum
  hardware was used.

## Citation

See [`CITATION.cff`](CITATION.cff). Please cite the paper if you use QVerdict.

## License

Code: MIT (see [`LICENSE`](LICENSE)). The collaborating authors should confirm the licence
choice before the public release.
