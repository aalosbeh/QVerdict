# Quantum Evidence Lab

A free local pilot for the proposed study **Learning to Verify Quantum Programs**.
Prepared 24 September 2026. All supplied results are simulated. No students,
human-subject data, cloud accounts, API keys, GPUs, or quantum processors were used.

## Start in five minutes

Use Python 3.12 in a fresh environment. The pinned environments were executed
with Python 3.12.14 on Linux. Installation needs internet; experiments run offline.

```bash
python -m venv .venv
```

Activate on macOS/Linux:

```bash
source .venv/bin/activate
```

Activate on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Then run:

```bash
python -m pip install -r requirements.txt
python experiment.py --out my_results
```

The `results/` directory already contains the completed reference run. Use a
different output folder to preserve it. `experiment.py` needs only NumPy and
SciPy. `Quantum_Evidence_Walkthrough.ipynb` provides a notebook introduction;
open it in a locally installed Jupyter environment or VS Code with notebook support.
The command-line route is sufficient and does not require Jupyter.

## Optional Qiskit example

Create a **separate** environment, activate it, and run:

```bash
python -m pip install -r requirements-qiskit.txt
python qiskit_example.py
```

This script writes `results/qiskit_check.json`. The Qiskit example uses local
StatevectorSampler and DensityMatrix, not IBM Runtime. It cross-checks all
17 states in three bases and prints one Bell-state comparison.

The two requirements files describe two separately tested environments. Do not
combine them. A different compatible package version can produce different
seeded counts; retain exact package versions when reproducing numerical outputs.

## What is implemented

- Seventeen deliberately chosen two-qubit density matrices, including equivalent
  controls, phase and bit errors, missing entanglement, incoherent and noisy mixtures,
  and cases near a fidelity threshold.
- Four methods: an intentionally inadequate Z-only teaching control; fixed XX/ZZ
  evidence; staged XX/ZZ evidence; and fixed XX/YY/ZZ evidence.
- Exact binomial confidence intervals with Bonferroni correction across measured
  observables and, for staged testing, all three prespecified looks.
- Outcomes: supported, contradicted, or inconclusive for the stated contract.
- Raw cumulative parity counts, per-run outcomes, aggregate summaries and metadata.
- Analytic checks and 200 random-density-matrix checks of the bounds, plus an
  independent Qiskit calculation of all 51 case/basis probabilities.

This is not an adaptive tutoring platform, a validated student assessment, an
AI-generated code corpus, a hardware experiment, or a state-of-the-art testing
benchmark. The proposed research extends this pilot; see the blueprint and protocol.

## Contract and mathematical scope

The output-state contract is fidelity F >= 0.90 with the Bell state Phi-plus.
Here F = <Phi-plus|rho|Phi-plus>, the overlap with a pure target, not its square root.
This evaluates one output state for a specified preparation; it does not prove
program equivalence on all inputs, identify a root cause, or establish security.

Let qX and qZ be the probabilities of odd parity when both qubits are measured
in X and Z. Phi-plus has even parity in both. Then:

    max(0, 1-qX-qZ) <= F <= 1-max(qX,qZ)

For YY the target has odd parity; define qY as the probability of even parity.
With the third measurement:

    F = 1-(qX+qY+qZ)/2

These relations follow from the Bell stabilizers and are established quantum
state-verification ideas, not novelty claims. See Pallister, Linden and Montanaro,
Physical Review Letters 120, 170502 (2018), DOI 10.1103/PhysRevLett.120.170502.

For each q, substitute simultaneous lower and upper Clopper-Pearson limits to
produce a fidelity interval. Support the contract only if its lower bound is at
least 0.90; contradict it only if its upper bound is below 0.90; otherwise abstain.
The 0.90 threshold is a chosen classroom specification, not an industry standard.

The fixed XX/ZZ method uses two intervals, each with failure probability 0.05/2.
The staged method uses two observables at three possible total budgets (96, 384,
1536), each interval with failure probability 0.05/6. There are no extra unplanned
looks. The three-basis fixed method uses 0.05/3. Intervals are two-sided. These are
per-state-run guarantees under independent, identically prepared samples and
trusted measurements. They are not a simultaneous 95% guarantee over the entire
benchmark. Hardware drift or biased measurement would require another model.

## Interpreting the pilot

Each of 17 cases has 400 independent repetition seeds. The four methods share
basis-specific samples within each repetition for paired comparisons. The
Z-only control uses the full budget but lacks phase information; it is deliberately
weak and is never the sole research comparator. Fixed methods use 1536 shots.
The staged method can stop at 96, 384 or 1536 shots.

The staged rule reduced the mean shots for this hand-selected suite while increasing
the inconclusive rate. The three-basis baseline resolved more cases. None of this
establishes algorithmic superiority, general industrial reliability, or educational
effectiveness. Counts from 400 repeats are not 400 independent circuit families.
In particular, the exact-threshold case cannot reliably be separated from the
boundary using finite samples. An inconclusive result is a scientifically valid
outcome, not a wrong decision.

The simple Z-only control checks correlation rather than full output distributions.
Even a full computational-basis distribution test cannot distinguish Phi-plus from
Phi-minus or the equally weighted incoherent mixture of 00 and 11. This is an
information limitation, not a failure that more Z measurements can fix.

## Files

| File | Purpose |
|---|---|
| experiment.py | Reproduce the statistical pilot |
| qiskit_example.py | Executable circuit example and independent probability checks |
| Quantum_Evidence_Walkthrough.ipynb | Instructor or collaborator notebook |
| STUDY_PROTOCOL.md | Proposed human study and validity safeguards |
| LAB_HANDOUT.md | A ready-to-try 60–90 minute lesson and instructor key |
| RESEARCH_BLUEPRINT.md | Full literature-grounded research and grant plan |
| results/trials.csv | One final result per case, repeat and method |
| results/observations.csv | Every observed stage including intermediate counts |
| results/summary.csv | Per-case descriptive results |
| results/results.json | Configuration, versions, source hash, outcomes and state catalog |
| results/qiskit_check.json | Qiskit verification and example counts |

## Attribution and release

All included code and lesson text were newly prepared for this project; no third-party
curriculum or restricted assessment items are redistributed. External resources keep
their own licenses. Before a public research release, the collaborators should agree
on authorship and choose a permissive code license and an appropriate Creative Commons
license for original teaching materials through their institutions. The package is
ready for local evaluation; it does not claim that institutional release approval,
IRB review, or peer review has already occurred.
