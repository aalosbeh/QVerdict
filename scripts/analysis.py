"""Loading and aggregation shared by make_figures.py and make_tables.py.

Every number printed in the paper is computed here from the CSV/JSON files in
results/, so text, tables and figures cannot drift apart.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
PAPER = ROOT / "paper"
TAU = 0.90
ALPHA = 0.05

NUMERIC = {"R", "n_pass", "n_fail", "n_inc", "n_wrong", "p_pass", "p_fail", "p_inc", "p_wrong", "flip",
           "shots_mean", "shots_median", "shots_p90", "settings_mean", "F", "F_ideal", "truth", "equivalent",
           "variant", "m", "k", "L_union", "U_union", "L_lp", "U_lp", "L_z", "U_z", "z_tvd", "z_tvd_ideal",
           "z_q", "exact_p", "inv_p0", "gates", "twoq", "budget", "readout", "n", "twoq_transpiled",
           "mean_readout_err"}

ORACLE_ORDER = ["Z-chi2", "ZX-chi2", "Pauli-tol", "Inverse-0tol", "Plugin-DFE", "CP-TG", "CP-DFE",
                "Peek-CP-TG", "QV-Z", "QV-TG", "QV-DFE", "QV-ESC", "QV-DFE-RC"]
FAMILY = {"Z-chi2": "Existing practice", "ZX-chi2": "Existing practice", "Pauli-tol": "Existing practice",
          "Inverse-0tol": "Existing practice", "Plugin-DFE": "Uncertainty-free",
          "CP-TG": "Fixed-sample certified", "CP-DFE": "Fixed-sample certified",
          "Peek-CP-TG": "Invalid sequential", "QV-Z": "Proposed", "QV-TG": "Proposed",
          "QV-DFE": "Proposed", "QV-ESC": "Proposed", "QV-DFE-RC": "Proposed"}
LATEX_NAME = {"Z-chi2": r"Z-$\chi^2$", "ZX-chi2": r"ZX-$\chi^2$", "Pauli-tol": "Pauli-tol",
              "Inverse-0tol": "Inverse-0", "Plugin-DFE": "Plug-in", "CP-TG": "CP-TG", "CP-DFE": "CP-DFE",
              "Peek-CP-TG": "Peek-CP", "QV-Z": "QV-Z", "QV-TG": "QV-TG", "QV-DFE": "QV-DFE",
              "QV-ESC": "QV-ESC", "QV-DFE-RC": "QV-DFE-RC"}


def load_csv(name: str) -> list[dict]:
    path = RES / name
    if not path.exists():
        return []
    out = []
    with open(path) as f:
        for r in csv.DictReader(f):
            for k in list(r):
                if k in NUMERIC and r[k] not in ("", None):
                    try:
                        r[k] = float(r[k])
                    except ValueError:
                        pass
            out.append(r)
    return out


def load_json(name: str):
    p = RES / name
    return json.loads(p.read_text()) if p.exists() else None


def pooled(rows, key=lambda r: r["oracle"]):
    """Pool verdict counts over rows, grouped by ``key``."""
    acc = defaultdict(lambda: defaultdict(float))
    for r in rows:
        a = acc[key(r)]
        R = r["R"]
        t = r["truth"]
        a["runs"] += R
        a["cases"] += 1
        a["wrong"] += r["n_wrong"]
        a["inc"] += r["n_inc"]
        a["pass"] += r["n_pass"]
        a["fail"] += r["n_fail"]
        a["shots"] += r["shots_mean"] * R
        a["settings"] += r["settings_mean"] * R
        a["flip"] += r["flip"]
        a["max_flip"] = max(a["max_flip"], r["flip"])
        a["max_wrong"] = max(a["max_wrong"], r["p_wrong"])
        # cases whose wrong rate exceeds alpha by more than 3 binomial SEs
        se = np.sqrt(ALPHA * (1 - ALPHA) / R)
        a["cases_over_alpha"] += float(r["p_wrong"] > ALPHA + 3 * se)
        if t:
            a["runs_sat"] += R
            a["false_fail"] += r["n_fail"]
            a["pass_sat"] += r["n_pass"]
            a["cases_sat"] += 1
        else:
            a["runs_viol"] += R
            a["false_pass"] += r["n_pass"]
            a["fail_viol"] += r["n_fail"]
            a["cases_viol"] += 1
    out = {}
    for k, a in acc.items():
        runs = a["runs"]
        out[k] = dict(
            cases=int(a["cases"]), runs=int(runs),
            wrong=a["wrong"] / runs, inc=a["inc"] / runs,
            false_pass=a["false_pass"] / a["runs_viol"] if a["runs_viol"] else float("nan"),
            false_fail=a["false_fail"] / a["runs_sat"] if a["runs_sat"] else float("nan"),
            kill=a["fail_viol"] / a["runs_viol"] if a["runs_viol"] else float("nan"),
            accept=a["pass_sat"] / a["runs_sat"] if a["runs_sat"] else float("nan"),
            decisive_acc=1 - a["wrong"] / max(a["pass"] + a["fail"], 1),
            shots=a["shots"] / runs, settings=a["settings"] / runs,
            flip=a["flip"] / a["cases"], max_flip=a["max_flip"], max_wrong=a["max_wrong"],
            cases_over_alpha=int(a["cases_over_alpha"]),
            cases_sat=int(a["cases_sat"]), cases_viol=int(a["cases_viol"]))
    return out


def shots_ratio(stats, a, b):
    return stats[b]["shots"] / stats[a]["shots"]
