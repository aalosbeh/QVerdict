# Can you trust this quantum program

Time: 60–90 minutes after an introduction to H, X, Z, CNOT and measurement.
Students need basic Python and probabilities. Supply a short vector and basis
refresher; no prior quantum physics course is required.

## Your assignment

A software team says its program prepares the Bell state Phi-plus from 00.
You receive two candidate implementations. Your job is to assess the claim,
write a discriminating test, and explain the scope of your conclusion.

```python
from qiskit import QuantumCircuit

def candidate_a():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    return qc

def candidate_b():
    qc = candidate_a()
    qc.z(0)
    return qc
```

These are instructor-prepared snippets. They are not a measured sample of AI
errors. In a later AI-assisted study, real model outputs must be identified and
archived with model, prompt, date, settings and licenses.

## Predict and justify

1. Before running anything, predict each circuit's Z-basis outcome distribution.
2. Would identical Z-basis histograms prove that the two output states are equal?
3. If you could spend 256 more shots, would you repeat Z measurements or change
   the measurement basis? Explain what information your choice adds.

## Execute

Follow README.md and run `python qiskit_example.py`. The script measures both
circuits in Z and X. X measurement is implemented by adding H to each qubit before
ordinary measurement. Each shot requires a newly prepared state. Do not measure
one copy in Z and then treat it as an untouched copy for an X measurement.

Use `results/qiskit_check.json` if you cannot install the optional environment.
The analytic expected distributions can be worked out without any SDK.

## Make a decision

Complete this evidence record for each circuit:

| Field | Your response |
|---|---|
| Claim | State the required output and input |
| Test | State the basis and property being checked |
| Prediction | Give the expected pattern before execution |
| Observation | Record shots, counts, seed and simulator version |
| Decision | Supported, contradicted, or inconclusive |
| Limit | State what the test does not establish |
| Next action | Repair, change basis, gather more evidence, or stop |

Run `python experiment.py --out my_results` and compare `fixed_XX_ZZ` with
`staged_XX_ZZ` and `fixed_XX_YY_ZZ`. Find a case where more measurement types help.
Find a case near the required fidelity for which an inconclusive answer is reasonable.

## Discipline extensions

- CS: write a regression test that catches the phase error and accepts a global
  phase change; explain why an output-state test is not whole-program equivalence.
- IT: document environment versions and reproduce the same decision in a second
  environment; distinguish an installation error from quantum sampling variation.
- IS: write a 150-word acceptance recommendation linking the business requirement
  to the technical evidence and its limits. Do not claim commercial quantum advantage.

## Instructor key

Candidate A prepares (00 + 11)/sqrt(2); candidate B prepares (00 - 11)/sqrt(2).
Both have 50% 00 and 50% 11 in Z. In X, A has only even parity and B only odd parity.
The phase error is invisible to any number of Z-only observations. A global phase
on the entire state changes neither distribution and is not a defect.

The supplied Qiskit run has 131 instances of 00 and 125 of 11 in Z for each circuit.
In X the target has 131 of 00 and 125 of 11; the faulty circuit has 131 of 01 and
125 of 10. Identical counts here arise from the controlled seed; actual independent
experiments need not have identical counts even when their distributions agree.

The statistical contract is F >= 0.90, where F is overlap with Phi-plus. This is
a pedagogical threshold selected for the exercise. The script's density matrices
are ground truth only for evaluating the teaching fixtures; a student performing
black-box tests is not given those matrices.

Rubric: claim accuracy 0–2; test choice 0–2; statistical interpretation 0–2;
decision and limitation 0–2; reproducibility 0–2. For research, use a separate
unseen transfer assessment and the protocol's more detailed scoring procedure.
