"""Generate the LaTeX tables and the numeric macros (paper/generated/numbers.tex).

Every quantitative statement in the manuscript is a macro defined here and
computed from results/, so the paper cannot silently disagree with the data.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np

from analysis import ALPHA, FAMILY, LATEX_NAME, ORACLE_ORDER, PAPER, TAU, load_csv, load_json, pooled

GEN = PAPER / "generated"
GEN.mkdir(parents=True, exist_ok=True)
MACROS: dict[str, str] = {}


def macro(name: str, value) -> None:
    assert name.isalpha(), name
    MACROS[name] = str(value)


def pct(x, d=1):
    return "--" if x != x else f"{100 * x:.{d}f}"


def write(name, text):
    (GEN / name).write_text(text)
    print("wrote", name)


# --------------------------------------------------------------- subjects
def table_subjects(cases, meta):
    lines = [r"\begin{tabular}{@{}llcccccccc@{}}", r"\toprule",
             r"Program & Contract & $n$ & $m$ & Gates & 2Q & Cover settings & Mutants & \multicolumn{2}{c}{Satisfying (\%)}\\",
             r"\cmidrule(l){9-10}", r" & & & & & & & & N0 & N2\\", r"\midrule"]
    total_mut = 0
    for s in meta["subjects"]:
        name = s["name"]
        sat = {nk: np.mean([r["truth"] for r in cases if r["subject"] == name and r["noise"] == nk])
               for nk in ("N0", "N2")}
        def fmt(x):
            if len(x) >= 3 and len(set(x)) == 1:
                return f"${x[0]}^{{\\otimes {len(x)}}}$"
            return x
        settings = ", ".join(fmt(x) for x in s["settings"]) if s["target"] == "stabilizer" else r"product basis"
        mut = s["variants"] - 1
        total_mut += mut
        contract = "process" if s["contract"] == "process" else "state"
        lines.append(f"{name} & {contract} & {s['n']} & {s['observed']} & {s['gates']} & {s['twoq']} & "
                     f"\\texttt{{\\footnotesize {settings}}} & {mut} & {100 * sat['N0']:.0f} & {100 * sat['N2']:.0f}\\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_subjects.tex", "\n".join(lines) + "\n")
    macro("numSubjects", len(meta["subjects"]))
    macro("numMutants", total_mut)
    macro("numVariants", total_mut + len(meta["subjects"]))
    macro("numCases", len(cases))
    macro("numStateSubjects", sum(1 for s in meta["subjects"] if s["contract"] == "state"))
    macro("numProcessSubjects", sum(1 for s in meta["subjects"] if s["contract"] == "process"))
    macro("maxQubits", max(s["n"] for s in meta["subjects"]))
    ops = defaultdict(int)
    for s in meta["subjects"]:
        for k, v in s["mutants_by_op"].items():
            ops[k] += v
    for k, v in ops.items():
        macro("numMut" + k.replace("Q", "Q"), v)
    macro("numSatisfying", int(sum(r["truth"] for r in cases)))
    macro("numViolating", int(len(cases) - sum(r["truth"] for r in cases)))
    macro("numEquivalent", int(sum(r["equivalent"] for r in cases if r["noise"] == "N0" and r["op"] != "ORIG")))


# -------------------------------------------------------------- main table
def table_main(rows, meta):
    st = pooled(rows)
    lines = [r"\begin{tabular}{@{}llrrrrrrrr@{}}", r"\toprule",
             r"Oracle & Class & Wrong & \makecell{Unsound\\PASS} & \makecell{False\\FAIL} & INC & "
             r"\makecell{Worst\\case} & \makecell{Cases\\$>\alpha$} & Flip & \makecell{Mean\\shots}\\",
             r"\midrule"]
    prev = None
    for o in ORACLE_ORDER:
        if o not in st:
            continue
        s = st[o]
        fam = FAMILY[o]
        if prev is not None and fam != prev:
            lines.append(r"\midrule")
        prev = fam
        bold = o in ("QV-TG", "QV-DFE", "QV-ESC")
        name = LATEX_NAME[o]
        cells = [pct(s["wrong"], 2), pct(s["false_pass"], 2), pct(s["false_fail"], 2), pct(s["inc"], 1),
                 pct(s["max_wrong"], 1), str(s["cases_over_alpha"]), pct(s["flip"], 2), f"{s['shots']:.0f}"]
        if bold:
            name = r"\textbf{" + name + "}"
        short = {"Existing practice": "existing", "Uncertainty-free": "plug-in",
                 "Fixed-sample certified": "fixed-$N$", "Invalid sequential": "peeking",
                 "Proposed": "proposed"}[fam]
        lines.append(f"{name} & {short} & " + " & ".join(cells) + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_main.tex", "\n".join(lines) + "\n")
    for o, key in (("Z-chi2", "Zchi"), ("ZX-chi2", "ZXchi"), ("Pauli-tol", "Pauli"), ("Inverse-0tol", "Inv"),
                   ("Plugin-DFE", "Plugin"), ("CP-TG", "CPTG"), ("CP-DFE", "CPDFE"), ("Peek-CP-TG", "Peek"),
                   ("QV-Z", "QVZ"), ("QV-TG", "QVTG"), ("QV-DFE", "QVDFE"), ("QV-ESC", "QVESC")):
        s = st[o]
        macro("wrong" + key, pct(s["wrong"], 2))
        macro("unsoundPass" + key, pct(s["false_pass"], 2))
        macro("falseFail" + key, pct(s["false_fail"], 2))
        macro("inc" + key, pct(s["inc"], 1))
        macro("worst" + key, pct(s["max_wrong"], 1))
        macro("overAlpha" + key, s["cases_over_alpha"])
        macro("flip" + key, pct(s["flip"], 2))
        macro("maxFlip" + key, pct(s["max_flip"], 1))
        macro("shots" + key, f"{s['shots']:.0f}")
        macro("kill" + key, pct(s["kill"], 1))
        macro("accept" + key, pct(s["accept"], 1))
        macro("settings" + key, f"{s['settings']:.1f}")
    macro("reps", int(rows[0]["R"]))
    macro("numOracleRuns", f"{sum(s['runs'] for s in st.values()):,}".replace(",", "{,}"))
    macro("shotSaveDFE", f"{meta['budget'] / st['QV-DFE']['shots']:.1f}")
    macro("shotSaveTG", f"{meta['budget'] / st['QV-TG']['shots']:.1f}")
    macro("shotSaveESC", f"{meta['budget'] / st['QV-ESC']['shots']:.1f}")
    macro("budget", f"{meta['budget']:,}".replace(",", "{,}"))
    macro("budgetRaw", meta["budget"])
    macro("batch", meta["batch"])
    macro("worstProposed", pct(max(st[o]["max_wrong"] for o in ("QV-TG", "QV-DFE", "QV-ESC", "QV-Z")), 1))
    macro("wrongProposedMax", pct(max(st[o]["wrong"] for o in ("QV-TG", "QV-DFE", "QV-ESC", "QV-Z")), 2))
    by_noise = pooled(rows, key=lambda r: (r["oracle"], r["noise"]))
    for nk in ("N0", "N1", "N2"):
        macro("wrongZchi" + nk.replace("N0", "Ideal").replace("N1", "Moderate").replace("N2", "Strong"),
              pct(by_noise[("Z-chi2", nk)]["wrong"], 1))
    return st


# ------------------------------------------------------- observability (RQ1)
def table_observability(cases, rows):
    subjects = []
    for r in cases:
        if r["subject"] not in subjects:
            subjects.append(r["subject"])
    zchi = {(r["subject"], r["variant"]): r for r in rows if r["oracle"] == "Z-chi2" and r["noise"] == "N0"}
    lines = [r"\begin{tabular}{@{}lrrrrrr@{}}", r"\toprule",
             r"Program & \makecell{Violating\\(N0)} & \makecell{Z-invisible\\(\%)} & "
             r"\makecell{Z-$\chi^2$ PASS on\\Z-invisible (\%)} & \multicolumn{3}{c}{Cover plan ambiguous (\%)}\\",
             r"\cmidrule(l){5-7}", r" & & & & N0 & N1 & N2\\", r"\midrule"]
    all_viol, all_inv, zpass_num, zpass_den = 0, 0, 0.0, 0.0
    gaps = []
    for s in subjects:
        n0 = [r for r in cases if r["subject"] == s and r["noise"] == "N0" and r["truth"] == 0]
        inv = [r for r in n0 if r["z_tvd_ideal"] < 1e-9]
        all_viol += len(n0)
        all_inv += len(inv)
        zp = [zchi[(s, r["variant"])] for r in inv]
        zrate = sum(z["n_pass"] for z in zp) / max(sum(z["R"] for z in zp), 1)
        zpass_num += sum(z["n_pass"] for z in zp)
        zpass_den += sum(z["R"] for z in zp)
        amb = []
        for nk in ("N0", "N1", "N2"):
            rs = [r for r in cases if r["subject"] == s and r["noise"] == nk]
            amb.append(100 * np.mean([(r["L_lp"] < TAU) and (r["U_lp"] >= TAU) for r in rs]))
            gaps += [r["L_lp"] - r["L_union"] for r in rs]
        lines.append(f"{s} & {len(n0)} & {100 * len(inv) / max(len(n0), 1):.1f} & "
                     f"{'--' if not inv else f'{100 * zrate:.1f}'} & " + " & ".join(f"{a:.1f}" for a in amb) + r"\\")
    lines += [r"\midrule",
              f"All & {all_viol} & {100 * all_inv / all_viol:.1f} & {100 * zpass_num / zpass_den:.1f} & "
              + " & ".join(f"{100 * np.mean([(r['L_lp'] < TAU) and (r['U_lp'] >= TAU) for r in cases if r['noise'] == nk]):.1f}"
                           for nk in ("N0", "N1", "N2")) + r"\\",
              r"\bottomrule", r"\end{tabular}"]
    write("tab_observability.tex", "\n".join(lines) + "\n")
    macro("numViolatingIdeal", all_viol)
    macro("numZInvisible", all_inv)
    macro("pctZInvisible", f"{100 * all_inv / all_viol:.1f}")
    macro("pctZchiPassInvisible", f"{100 * zpass_num / zpass_den:.1f}")
    per = []
    for s in subjects:
        n0 = [r for r in cases if r["subject"] == s and r["noise"] == "N0" and r["truth"] == 0]
        if n0 and s != "BV-5":
            per.append(100 * np.mean([r["z_tvd_ideal"] < 1e-9 for r in n0]))
    macro("pctZInvisibleMin", f"{min(per):.0f}")
    macro("pctZInvisibleMax", f"{max(per):.0f}")
    two = [r["L_lp"] - r["L_union"] for r in cases if r["k"] == 2]
    three = [r["L_lp"] - r["L_union"] for r in cases if r["k"] == 3]
    macro("maxGapTwo", f"{max(two):.1e}".replace("e-", r"\times 10^{-") + "}" if max(two) > 0 else "0")
    macro("maxGapThree", f"{max(three):.3f}")
    for nk in ("N0", "N1", "N2"):
        amb = 100 * np.mean([(r["L_lp"] < TAU) and (r["U_lp"] >= TAU) for r in cases if r["noise"] == nk])
        macro("ambCover" + {"N0": "Ideal", "N1": "Moderate", "N2": "Strong"}[nk], f"{amb:.1f}")
    zfail_only = [r for r in cases if r["subject"] != "BV-5" and r["target"] == "stabilizer"]
    macro("zPassIdentifiable", sum(1 for r in zfail_only if r["L_z"] >= TAU))


# ----------------------------------------------------- mutation analysis (RQ4)
def table_mutation(rows):
    show = ["Z-chi2", "ZX-chi2", "Pauli-tol", "Inverse-0tol", "Plugin-DFE", "CP-DFE", "QV-TG", "QV-DFE", "QV-ESC"]
    lines = [r"\begin{tabular}{@{}llr" + "r" * len(show) + r"@{}}", r"\toprule",
             r"Noise & Operator & \#viol. & " + " & ".join(LATEX_NAME[o] for o in show) + r"\\", r"\midrule"]
    for nk in ("N0", "N1"):
        for op in ("QGD", "QGI", "QGR", "RGI", "all"):
            sel = [r for r in rows if r["noise"] == nk and r["op"] != "ORIG" and (op == "all" or r["op"] == op)
                   and r["truth"] == 0]
            nviol = len({(r["subject"], r["variant"]) for r in sel})
            cells = []
            for o in show:
                s = [r for r in sel if r["oracle"] == o]
                cells.append(pct(sum(r["n_fail"] for r in s) / max(sum(r["R"] for r in s), 1), 1))
            label = op if op != "all" else r"\textit{all}"
            lines.append(f"{nk if op == 'QGD' else ''} & {label} & {nviol} & " + " & ".join(cells) + r"\\")
        # false alarms on contract-satisfying mutants
        sel = [r for r in rows if r["noise"] == nk and r["op"] != "ORIG" and r["truth"] == 1]
        nsat = len({(r["subject"], r["variant"]) for r in sel})
        cells = [pct(sum(r["n_fail"] for r in sel if r["oracle"] == o) /
                     max(sum(r["R"] for r in sel if r["oracle"] == o), 1), 1) for o in show]
        lines.append(r" & \textit{false alarm}$^\dagger$ & " + str(nsat) + " & " + " & ".join(cells) + r"\\")
        if nk == "N0":
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_mutation.tex", "\n".join(lines) + "\n")
    for o, key in (("QV-DFE", "QVDFE"), ("QV-TG", "QVTG"), ("QV-ESC", "QVESC"), ("Z-chi2", "Zchi"),
                   ("ZX-chi2", "ZXchi"), ("Pauli-tol", "Pauli"), ("Inverse-0tol", "Inv"),
                   ("CP-DFE", "CPDFE"), ("Plugin-DFE", "Plugin")):
        for nk in ("N0", "N1"):
            sel = [r for r in rows if r["noise"] == nk and r["op"] != "ORIG" and r["truth"] == 0 and r["oracle"] == o]
            macro("killMut" + key + {"N0": "Ideal", "N1": "Moderate"}[nk],
                  pct(sum(r["n_fail"] for r in sel) / sum(r["R"] for r in sel), 1))
            sel = [r for r in rows if r["noise"] == nk and r["op"] != "ORIG" and r["truth"] == 1 and r["oracle"] == o]
            macro("alarmMut" + key + {"N0": "Ideal", "N1": "Moderate"}[nk],
                  pct(sum(r["n_fail"] for r in sel) / sum(r["R"] for r in sel), 1))


# ------------------------------------------------------------- boundary (RQ2)
def boundary_numbers():
    rows = load_csv("boundary.csv")
    if not rows:
        return
    worst = defaultdict(float)
    for r in rows:
        worst[r["oracle"]] = max(worst[r["oracle"]], r["p_wrong"])
    for o, key in (("Plugin-DFE", "Plugin"), ("Peek-CP-TG", "Peek"), ("CP-DFE", "CPDFE"), ("CP-TG", "CPTG"),
                   ("QV-TG", "QVTG"), ("QV-DFE", "QVDFE"), ("QV-ESC", "QVESC"), ("Z-chi2", "Zchi"),
                   ("ZX-chi2", "ZXchi"), ("Inverse-0tol", "Inv"), ("Pauli-tol", "Pauli"), ("QV-Z", "QVZ")):
        macro("bWorst" + key, pct(worst[o], 1))
    macro("bWorstProposed", pct(max(worst[o] for o in ("QV-TG", "QV-DFE", "QV-ESC", "QV-Z")), 2))
    meta = load_json("boundary_meta.json")
    macro("bReps", f"{meta['reps']:,}".replace(",", "{,}"))
    macro("bPoints", len(meta["F_grid"]))
    sel = {(r["oracle"], r["F"]): r for r in rows if r["subject"] == "GHZ-4" and r["family"] == "coherent"}
    for F, key in ((0.94, "NinetyFour"), (0.96, "NinetySix"), (1.0, "One")):
        macro("bShotsQVDFE" + key, f"{sel[('QV-DFE', F)]['shots_mean']:.0f}")
        macro("bShotsQVTG" + key, f"{sel[('QV-TG', F)]['shots_mean']:.0f}")
    macro("bPassQVDFEninetytwo", pct(sel[("QV-DFE", 0.92)]["p_pass"], 1))
    macro("bPassCPDFEninetytwo", pct(sel[("CP-DFE", 0.92)]["p_pass"], 1))
    macro("bPassPlugNinetyFive", pct(sel[("Plugin-DFE", 0.895)]["p_pass"], 1))


# ------------------------------------------------------------ tau (RQ2/3)
def table_tau(rows_main):
    show = ["Plugin-DFE", "CP-TG", "CP-DFE", "QV-TG", "QV-DFE", "QV-ESC"]
    lines = [r"\begin{tabular}{@{}lrrrrrrrrr@{}}", r"\toprule",
             r" & \multicolumn{3}{c}{$\tau=0.80$} & \multicolumn{3}{c}{$\tau=0.90$} & \multicolumn{3}{c}{$\tau=0.95$}\\",
             r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(l){8-10}",
             r"Oracle & Worst & INC & Shots & Worst & INC & Shots & Worst & INC & Shots\\", r"\midrule"]
    data = {0.9: pooled(rows_main)}
    for t in (0.8, 0.95):
        r = load_csv(f"benchmark_tau{t:g}.csv")
        if r:
            data[t] = pooled(r)
    for o in show:
        cells = []
        for t in (0.8, 0.9, 0.95):
            s = data.get(t, {}).get(o)
            cells += ["--"] * 3 if s is None else [pct(s["max_wrong"], 1), pct(s["inc"], 1), f"{s['shots']:.0f}"]
        lines.append(LATEX_NAME[o] + " & " + " & ".join(cells) + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_tau.tex", "\n".join(lines) + "\n")
    worst = max(data[t][o]["max_wrong"] for t in data for o in ("QV-TG", "QV-DFE", "QV-ESC"))
    macro("tauWorstProposed", pct(worst, 1))
    macro("tauWorstPlugin", pct(max(data[t]["Plugin-DFE"]["max_wrong"] for t in data), 1))


# ------------------------------------------------------------- cost (RQ3)
def cost_numbers():
    b = load_csv("budget.csv")
    if b:
        def inc(o, B):
            sel = [r for r in b if r["oracle"] == o and r["budget"] == B]
            return sum(r["n_inc"] for r in sel) / sum(r["R"] for r in sel)
        macro("incQVDFEsmall", pct(inc("QV-DFE", 1024), 1))
        macro("incQVDFElarge", pct(inc("QV-DFE", 32768), 1))
        macro("incCPDFElarge", pct(inc("CP-DFE", 32768), 1))
        macro("incQVTGlarge", pct(inc("QV-TG", 32768), 1))
        macro("incQVESClarge", pct(inc("QV-ESC", 32768), 1))
        macro("numBudgetCases", len({(r["subject"], r["variant"], r["noise"]) for r in b}))
    sc = load_csv("scaling.csv")
    if sc:
        g = {(r["family"], int(r["n"]), r["oracle"]): r for r in sc}
        macro("scaleTGpassTen", pct(g[("GHZ", 10, "QV-TG")]["p_pass"], 1))
        macro("scaleESCpassTen", pct(g[("GHZ", 10, "QV-ESC")]["p_pass"], 1))
        macro("scaleDFEsettingsTen", f"{g[('GHZ', 10, 'QV-DFE')]['settings_mean']:.0f}")
        macro("scaleESCsettingsFive", f"{g[('GHZ', 5, 'QV-ESC')]['settings_mean']:.1f}")
        macro("scaleDFEsettingsFive", f"{g[('GHZ', 5, 'QV-DFE')]['settings_mean']:.1f}")
        macro("scaleLunionNine", f"{g[('GHZ', 9, 'QV-TG')]['L_union']:.3f}")
        macro("scaleLunionTen", f"{g[('GHZ', 10, 'QV-TG')]['L_union']:.3f}")
        macro("scaleFTen", f"{g[('GHZ', 10, 'QV-TG')]['F']:.3f}")
        macro("scaleDFEshotsTen", f"{g[('GHZ', 10, 'QV-DFE')]['shots_mean']:.0f}")
        macro("scaleDFEshotsTwo", f"{g[('GHZ', 2, 'QV-DFE')]['shots_mean']:.0f}")


# ------------------------------------------------------- robustness (RQ5)
def robustness(rows_main):
    ro = load_csv("readout.csv")
    if ro:
        for r_, key in ((0.01, "One"), (0.02, "Two"), (0.04, "Four")):
            st = pooled([r for r in ro if r["readout"] == r_])
            for o, k in (("QV-DFE", "QVDFE"), ("QV-TG", "QVTG"), ("QV-DFE-RC", "RC"), ("Plugin-DFE", "Plugin"),
                         ("CP-DFE", "CPDFE")):
                macro("roFF" + k + key, pct(st[o]["false_fail"], 1))
                macro("roFP" + k + key, pct(st[o]["false_pass"], 2))
                macro("roWorst" + k + key, pct(st[o]["max_wrong"], 1))
        st_all = pooled([r for r in ro if r["readout"] > 0])
        macro("roMaxUnsoundPass", pct(max(v["false_pass"] for v in st_all.values()), 3))
        # readout-induced unsound passes (Z-chi2 excluded: its unsound passes stem from phase blindness)
        macro("roMaxUnsoundPassUncorr", pct(max(v["false_pass"] for k, v in st_all.items()
                                                 if k not in ("QV-DFE-RC", "Z-chi2")), 3))
        macro("roZchiUnsoundPass", pct(st_all["Z-chi2"]["false_pass"], 1))
    dev = load_csv("device.csv")
    if not dev:
        return
    show = ["Z-chi2", "ZX-chi2", "Pauli-tol", "Inverse-0tol", "Plugin-DFE", "CP-DFE", "QV-TG", "QV-DFE",
            "QV-ESC", "QV-DFE-RC"]
    devices = sorted({r["device"] for r in dev})
    lines = [r"\begin{tabular}{@{}l" + "rr" * len(devices) * 2 + r"@{}}", r"\toprule",
             " & " + " & ".join(rf"\multicolumn{{4}}{{c}}{{{d.replace('Fake', 'ibm\\_').lower()}}}" for d in devices) + r"\\",
             "".join(rf"\cmidrule(lr){{{2 + 4 * i}-{5 + 4 * i}}}" for i in range(len(devices))),
             " & " + " & ".join([r"\multicolumn{2}{c}{no readout err.} & \multicolumn{2}{c}{with readout err.}"] * len(devices)) + r"\\",
             "Oracle" + " & Wrong & INC" * 2 * len(devices) + r"\\", r"\midrule"]
    stats = {(d, ro_on): pooled([r for r in dev if r["device"] == d and r["readout"] == ro_on])
             for d in devices for ro_on in (0, 1)}
    for o in show:
        cells = []
        for d in devices:
            for ro_on in (0, 1):
                s = stats[(d, ro_on)].get(o)
                cells += ["--", "--"] if s is None else [pct(s["wrong"], 1), pct(s["inc"], 1)]
        name = LATEX_NAME[o]
        if o == "QV-DFE-RC":
            lines.append(r"\midrule")
            name = r"\textbf{" + name + "}"
        lines.append(name + " & " + " & ".join(cells) + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_device.tex", "\n".join(lines) + "\n")
    for d in devices:
        dk = d.replace("Fake", "")
        for ro_on, rk in ((0, "Clean"), (1, "Readout")):
            s = stats[(d, ro_on)]
            macro("dev" + dk + rk + "QVDFE", pct(s["QV-DFE"]["wrong"], 1))
            macro("dev" + dk + rk + "RC", pct(s["QV-DFE-RC"]["wrong"], 1))
            macro("dev" + dk + rk + "RCinc", pct(s["QV-DFE-RC"]["inc"], 1))
            macro("dev" + dk + rk + "RCshots", f"{s['QV-DFE-RC']['shots']:.0f}")
            macro("dev" + dk + rk + "Zchi", pct(s["Z-chi2"]["wrong"], 1))
            macro("dev" + dk + rk + "Plugin", pct(s["Plugin-DFE"]["wrong"], 1))
        orig = [r for r in dev if r["device"] == d and r["variant"] == 0 and r["oracle"] == "QV-DFE" and r["readout"] == 0]
        macro("dev" + dk + "ReadoutMean", pct(np.mean([r["mean_readout_err"] for r in orig]), 1))
        macro("dev" + dk + "Fmin", f"{min(r['F'] for r in orig):.3f}")
        macro("dev" + dk + "Fmax", f"{max(r['F'] for r in orig):.3f}")
    meta = load_json("device_meta.json")
    macro("devMutants", meta["mutants_per_subject"])
    macro("devSubjects", len(meta["subjects"]))
    macro("devCases", len({(r["device"], r["subject"], r["variant"]) for r in dev}))


def environment_numbers():
    xv = load_json("crossval_qiskit.json")
    if xv:
        macro("xvCount", xv["comparisons"])
        e = f"{xv['max_abs_diff']:.1e}"
        mant, ex = e.split("e")
        macro("xvMaxDiff", rf"{mant}\times 10^{{{int(ex)}}}")
        macro("qiskitVersion", xv["qiskit"])
        macro("aerVersion", xv["qiskit_aer"])
    meta = load_json("benchmark_meta.json")
    env = meta["environment"]
    macro("pyVersion", env["python"])
    macro("numpyVersion", env["numpy"])
    macro("scipyVersion", env["scipy"])
    macro("benchSeconds", f"{meta['elapsed_s']:.0f}")
    macro("escFraction", f"{meta['esc_fraction']:.2f}")
    macro("escWarmup", meta["esc_warmup"])


def extra_numbers(cases, rows):
    inv = {(r["subject"], r["variant"]) for r in cases
           if r["noise"] == "N0" and r["truth"] == 0 and r["z_tvd_ideal"] < 1e-9}
    z = [r for r in rows if r["oracle"] == "Z-chi2" and r["truth"] == 0]
    tot = sum(r["n_pass"] for r in z)
    macro("zchiUnsoundFromInvisible", f"{100 * sum(r['n_pass'] for r in z if (r['subject'], r['variant']) in inv) / tot:.0f}")
    noisy = np.array([r["shots_mean"] for r in rows if r["oracle"] == "QV-DFE" and r["noise"] in ("N1", "N2")])
    macro("medianShotsQVDFE", f"{np.median(noisy):.0f}")
    macro("shareDecidedFiveTwelve", f"{100 * np.mean(noisy <= 512):.0f}")
    three = [r for r in cases if r["k"] == 3]
    gap = max(max(r["L_lp"] - r["L_union"], r["U_union"] - r["U_lp"]) for r in three)
    macro("numThreeSettingCases", len(three))
    macro("maxGapThreeExact", "0" if gap < 1e-12 else f"{gap:.3g}")


def main():
    cases = load_csv("cases.csv")
    rows = load_csv("benchmark.csv")
    meta = load_json("benchmark_meta.json")
    table_subjects(cases, meta)
    table_main(rows, meta)
    table_observability(cases, rows)
    table_mutation(rows)
    boundary_numbers()
    table_tau(rows)
    cost_numbers()
    robustness(rows)
    environment_numbers()
    extra_numbers(cases, rows)
    macro("tauValue", f"{TAU:.2f}")
    macro("alphaValue", f"{ALPHA:.2f}")
    text = "% Auto-generated by scripts/make_tables.py -- do not edit by hand.\n"
    text += "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in sorted(MACROS.items()))
    write("numbers.tex", text)


if __name__ == "__main__":
    main()
