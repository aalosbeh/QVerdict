#!/usr/bin/env bash
# Reproduce every result, figure and table of the paper (about 25 minutes on a
# 16-core laptop).  Qiskit-dependent steps are skipped if Qiskit is missing.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python}
$PY -m pytest -q ../tests
$PY run_benchmark.py --reps 1000
$PY run_benchmark.py --reps 200 --tau 0.8  --oracles Plugin-DFE,CP-TG,CP-DFE,QV-TG,QV-DFE,QV-ESC
$PY run_benchmark.py --reps 200 --tau 0.95 --oracles Plugin-DFE,CP-TG,CP-DFE,QV-TG,QV-DFE,QV-ESC
$PY run_boundary.py  --reps 2000
$PY run_cost.py      --reps 100
$PY run_readout.py   --reps 200
if $PY -c "import qiskit_aer, qiskit_ibm_runtime" 2>/dev/null; then
  $PY crossval_qiskit.py
  $PY run_device.py --reps 200
else
  echo "Qiskit not installed: skipping crossval_qiskit.py and run_device.py"
fi
$PY ../scripts/make_figures.py
$PY ../scripts/make_tables.py
