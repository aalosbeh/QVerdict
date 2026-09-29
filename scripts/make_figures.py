"""Generate every data figure of the paper as vector PDF (IEEE column widths).

Colours follow a fixed oracle -> slot mapping (validated categorical palette);
every series also carries a distinct marker and line style so the figures
remain readable in grayscale and under colour-vision deficiencies.
"""
from __future__ import annotations

from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from analysis import ALPHA, PAPER, TAU, load_csv, load_json  # noqa: E402

FIG = PAPER / "figures"
FIG.mkdir(parents=True, exist_ok=True)
ONE, TWO = 3.5, 7.16  # IEEE single / double column widths (inches)

STYLE = {  # oracle: (colour, marker, linestyle, label)
    "QV-DFE": ("#2a78d6", "o", "-", "QV-DFE"),
    "Plugin-DFE": ("#eb6834", "^", ":", "Plug-in (no CI)"),
    "QV-TG": ("#1baf7a", "s", "-", "QV-TG"),
    "Peek-CP-TG": ("#eda100", "x", "--", "Peek-CP (invalid)"),
    "CP-DFE": ("#e87ba4", "v", "--", "CP-DFE (fixed $N$)"),
    "QV-ESC": ("#008300", "D", "-", "QV-ESC"),
    "QV-DFE-RC": ("#4a3aa7", "P", "-", "QV-DFE-RC"),
    "Z-chi2": ("#e34948", "*", ":", r"Z-$\chi^2$"),
    "CP-TG": ("#8a8985", "<", "--", "CP-TG (fixed $N$)"),
}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "mathtext.fontset": "stix", "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "legend.fontsize": 6.8, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.6, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.5, "grid.linestyle": "-",
    "lines.linewidth": 1.2, "lines.markersize": 3.6, "legend.frameon": False,
    "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})


def _line(ax, x, y, oracle, **kw):
    c, m, ls, lab = STYLE[oracle]
    ax.plot(x, y, color=c, marker=m, linestyle=ls, label=lab, markeredgewidth=0.6,
            markerfacecolor="white" if m not in ("x", "*", "P") else c, **kw)


def _save(fig, name):
    fig.savefig(FIG / f"{name}.pdf")
    fig.savefig(FIG / f"{name}.png", dpi=220)
    plt.close(fig)
    print("wrote", name)


# ------------------------------------------------------------------ Fig. 2
def fig_identifiability():
    """Identified fidelity regions of the {XX, ZZ} plan for the Bell target."""
    from matplotlib.patches import Polygon, Rectangle
    e = 1 - TAU
    lim = 0.24
    fig, ax = plt.subplots(figsize=(ONE, 2.6))
    ax.add_patch(Polygon([(0, 0), (lim, 0), (lim, lim), (0, lim)], closed=True, fc="#fbd9c9", ec="none"))
    ax.add_patch(Polygon([(0, 0), (e, 0), (e, e), (0, e)], closed=True, fc="#f0efec", ec="none"))
    ax.add_patch(Polygon([(0, 0), (e, 0), (0, e)], closed=True, fc="#cde2fb", ec="none"))
    ax.set_xlim(0, lim)
    ax.set_ylim(-0.004, lim)
    ax.set_xlabel(r"$q_X$: probability of odd parity in $XX$")
    ax.set_ylabel(r"$q_Z$: probability of odd parity in $ZZ$")
    ax.grid(False)
    ax.set_axisbelow(False)
    ax.text(0.004, 0.04, "PASS\n" + r"($L^\star\geq\tau$)", fontsize=6.8, color="#184f95")
    ax.text(0.135, 0.19, "FAIL\n" + r"($U^\star<\tau$)", fontsize=6.8, color="#9a3a12", ha="center")
    ax.text(0.068, 0.078, "ambiguous", fontsize=6.8, color=MUTED, ha="center")
    # coherent over-rotation: q_Z = 0, exactly identified
    th = np.linspace(0, np.arccos(1 - 2 * lim), 200)
    ax.plot((1 - np.cos(th)) / 2, 0 * th, color="#2a78d6", lw=2.0, solid_capstyle="butt", clip_on=False)
    ax.annotate("coherent $R_z(\\theta)$: $L^\\star=U^\\star=F$", xy=(0.17, 0.0), xytext=(0.128, 0.035),
                fontsize=6.4, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5))
    lam = np.linspace(0, 2 * lim, 200)
    ax.plot(lam / 2, lam / 2, color="#eb6834", lw=1.2, linestyle="--")
    ax.annotate("global depolarizing", xy=(0.16, 0.16), xytext=(0.168, 0.118),
                fontsize=6.4, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5))
    ax.add_patch(Rectangle((0.036, 0.007), 0.024, 0.019, fill=False, ec=INK, lw=0.7))
    ax.annotate("confidence box after $t$ shots:\nevery point has $L\\geq\\tau$ $\\Rightarrow$ PASS", xy=(0.06, 0.02), xytext=(0.128, 0.064), fontsize=6.4,
                color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5))
    ax.plot([0], [0], marker="o", color=INK, ms=4, clip_on=False, zorder=5)
    ax.annotate(r"$|\Phi^+\rangle$", xy=(0, 0), xytext=(0.004, 0.006), fontsize=7)
    _save(fig, "fig_identifiability")


# ------------------------------------------------------------------ Fig. 3
def fig_observability():
    cases = [r for r in load_csv("cases.csv")]
    subjects = []
    for r in cases:
        if r["subject"] not in subjects:
            subjects.append(r["subject"])
    zinv, amb1, amb2 = [], [], []
    for s in subjects:
        n0 = [r for r in cases if r["subject"] == s and r["noise"] == "N0" and r["truth"] == 0]
        zinv.append(100 * np.mean([r["z_tvd_ideal"] < 1e-9 for r in n0]) if n0 else 0)
        for store, nk in ((amb1, "N1"), (amb2, "N2")):
            rs = [r for r in cases if r["subject"] == s and r["noise"] == nk]
            store.append(100 * np.mean([(r["L_lp"] < TAU) and (r["U_lp"] >= TAU) for r in rs]))
    y = np.arange(len(subjects))
    fig, ax = plt.subplots(figsize=(ONE, 2.9))
    h = 0.27
    ax.barh(y - h, zinv, height=h * 0.92, color="#e34948", label="violating mutants invisible in Z basis")
    ax.barh(y, amb1, height=h * 0.92, color="#86b6ef", label="cover plan structurally ambiguous (N1)")
    ax.barh(y + h, amb2, height=h * 0.92, color="#1c5cab", label="cover plan structurally ambiguous (N2)")
    for yy, v in zip(y - h, zinv):
        ax.text(v + 1, yy, f"{v:.0f}", va="center", fontsize=5.8, color=MUTED)
    ax.set_yticks(y, subjects)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("share of variants (%)")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=1, handlelength=1.2)
    _save(fig, "fig_observability")


# ------------------------------------------------------------------ Fig. 4
def fig_boundary():
    rows = load_csv("boundary.csv")
    show = ["Plugin-DFE", "Peek-CP-TG", "CP-DFE", "QV-TG", "QV-DFE", "QV-ESC"]
    Fs = sorted({r["F"] for r in rows})
    fig, axs = plt.subplots(1, 3, figsize=(TWO, 2.05))
    # (a) worst wrong rate over subjects x families at each F
    for o in show:
        y = [max(r["p_wrong"] for r in rows if r["oracle"] == o and r["F"] == F) for F in Fs]
        _line(axs[0], Fs, np.array(y) * 100, o)
    axs[0].axhline(ALPHA * 100, color=INK, lw=0.7)
    axs[0].text(0.801, ALPHA * 100 + 1.2, r"$\alpha$ = 5%", fontsize=6.5)
    axs[0].axvline(TAU, color=MUTED, lw=0.5)
    axs[0].set_ylabel("worst wrong-verdict rate (%)")
    axs[0].set_xlabel("true fidelity $F$")
    axs[0].set_title("(a) worst case, 5 programs $\\times$ 2 fault types", loc="left")
    # (b) P(PASS) for GHZ-4, coherent
    sel = [r for r in rows if r["subject"] == "GHZ-4" and r["family"] == "coherent"]
    for o in show:
        y = [next(r["p_pass"] for r in sel if r["oracle"] == o and r["F"] == F) for F in Fs]
        _line(axs[1], Fs, np.array(y) * 100, o)
    axs[1].axvline(TAU, color=MUTED, lw=0.5)
    axs[1].set_ylabel("P(PASS) (%)")
    axs[1].set_xlabel("true fidelity $F$")
    axs[1].set_title("(b) GHZ-4, coherent over-rotation", loc="left")
    # (c) mean shots, GHZ-4 coherent
    for o in show:
        y = [next(r["shots_mean"] for r in sel if r["oracle"] == o and r["F"] == F) for F in Fs]
        _line(axs[2], Fs, y, o)
    axs[2].set_yscale("log", base=2)
    axs[2].axvline(TAU, color=MUTED, lw=0.5)
    axs[2].set_ylabel("mean shots")
    axs[2].set_xlabel("true fidelity $F$")
    axs[2].set_title("(c) cost, GHZ-4, coherent", loc="left")
    h, lab = axs[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.1), handlelength=2.2)
    fig.tight_layout(w_pad=1.0)
    _save(fig, "fig_boundary")


# ------------------------------------------------------------------ Fig. 5
def fig_cost():
    rows = [r for r in load_csv("benchmark.csv") if r["noise"] in ("N1", "N2")]
    budget = load_csv("budget.csv")
    fig, axs = plt.subplots(1, 2, figsize=(TWO, 2.1))
    for o in ["QV-DFE", "QV-TG", "QV-ESC", "Peek-CP-TG"]:
        s = np.sort([r["shots_mean"] for r in rows if r["oracle"] == o])
        c, m, ls, lab = STYLE[o]
        axs[0].step(s, np.arange(1, len(s) + 1) / len(s) * 100, where="post", color=c, linestyle=ls, label=lab)
    axs[0].axvline(8192, color=INK, lw=0.7)
    axs[0].text(8192 * 0.93, 30, "fixed-$N$ oracles", rotation=90, ha="right", fontsize=6.5)
    axs[0].set_xscale("log", base=2)
    axs[0].set_xlabel("mean shots per case (log scale)")
    axs[0].set_ylabel("cumulative share of cases (%)")
    axs[0].set_title("(a) shots to verdict, all N1/N2 cases", loc="left")
    axs[0].legend(loc="lower right", bbox_to_anchor=(0.86, 0.03))
    Bs = sorted({r["budget"] for r in budget})
    for o in ["CP-TG", "CP-DFE", "QV-TG", "QV-DFE", "QV-ESC"]:
        y = []
        for B in Bs:
            sel = [r for r in budget if r["oracle"] == o and r["budget"] == B]
            y.append(100 * sum(r["n_inc"] for r in sel) / sum(r["R"] for r in sel))
        _line(axs[1], Bs, y, o)
    axs[1].set_xscale("log", base=2)
    axs[1].set_xlabel("shot budget $N$")
    axs[1].set_ylabel("INCONCLUSIVE (%)")
    axs[1].set_title("(b) resolution vs budget (originals + RGI mutants)", loc="left")
    axs[1].legend(loc="upper right", ncol=1)
    fig.tight_layout(w_pad=1.2)
    _save(fig, "fig_cost")


# ------------------------------------------------------------------ Fig. 6
def fig_scaling():
    rows = load_csv("scaling.csv")
    fig, axs = plt.subplots(1, 2, figsize=(TWO, 2.0))
    for fam, mk_alpha in (("GHZ", 1.0), ("Cluster", 0.45)):
        for o in ["QV-TG", "QV-DFE", "QV-ESC"]:
            sel = sorted([r for r in rows if r["family"] == fam and r["oracle"] == o], key=lambda r: r["n"])
            n = [r["n"] for r in sel]
            c, m, ls, lab = STYLE[o]
            kw = dict(color=c, marker=m, alpha=mk_alpha, markerfacecolor="white", markeredgewidth=0.6,
                      linestyle="-" if fam == "GHZ" else ":", label=f"{lab} ({fam})")
            axs[0].plot(n, [r["shots_mean"] for r in sel], **kw)
            axs[1].plot(n, [r["settings_mean"] for r in sel], **kw)
    axs[0].set_yscale("log", base=2)
    axs[1].set_yscale("log", base=2)
    for a in axs:
        a.set_xlabel("qubits $n$")
    axs[0].set_ylabel("mean shots (budget 32768)")
    axs[1].set_ylabel("distinct measurement settings")
    axs[0].set_title("(a) shots to verdict under N1", loc="left")
    axs[1].set_title("(b) circuit variants to compile and run", loc="left")
    axs[1].legend(loc="upper left", ncol=2, fontsize=6.2)
    fig.tight_layout(w_pad=1.2)
    _save(fig, "fig_scaling")


# ------------------------------------------------------------------ Fig. 7
def fig_robustness():
    ro = load_csv("readout.csv")
    dev = load_csv("device.csv")
    fig, axs = plt.subplots(1, 2, figsize=(TWO, 2.15), gridspec_kw={"width_ratios": [1, 1.25]})
    rs = sorted({r["readout"] for r in ro})
    for o in ["Z-chi2", "Plugin-DFE", "CP-DFE", "QV-TG", "QV-DFE", "QV-DFE-RC"]:
        y = []
        for r_ in rs:
            sel = [r for r in ro if r["oracle"] == o and r["readout"] == r_ and r["truth"] == 1]
            y.append(100 * sum(r["n_fail"] for r in sel) / sum(r["R"] for r in sel))
        _line(axs[0], np.array(rs) * 100, y, o)
    axs[0].set_xlabel("symmetric readout flip probability $r$ (%)")
    axs[0].set_ylabel("false FAIL on satisfying cases (%)")
    axs[0].set_title("(a) readout sweep (N1 gate noise)", loc="left")
    axs[0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.33), fontsize=6.0, ncol=3)
    if dev:
        oracles = ["Z-chi2", "Plugin-DFE", "CP-DFE", "QV-TG", "QV-DFE", "QV-ESC", "QV-DFE-RC"]
        devices = sorted({r["device"] for r in dev})
        x = np.arange(len(oracles))
        w = 0.19
        k = 0
        shades = {("FakeSherbrooke", 0): "#86b6ef", ("FakeSherbrooke", 1): "#1c5cab",
                  ("FakeTorino", 0): "#f5b597", ("FakeTorino", 1): "#b8471b"}
        for d in devices:
            for ro_on in (0, 1):
                y = []
                for o in oracles:
                    sel = [r for r in dev if r["device"] == d and r["oracle"] == o and r["readout"] == ro_on]
                    y.append(100 * sum(r["n_wrong"] for r in sel) / sum(r["R"] for r in sel))
                lab = f"{d.replace('Fake', '')}, {'with' if ro_on else 'no'} readout error"
                axs[1].bar(x + (k - 1.5) * w, y, width=w * 0.9, color=shades[(d, ro_on)], label=lab)
                k += 1
        axs[1].set_xticks(x, [STYLE[o][3].replace(" (fixed $N$)", "").replace(" (no CI)", "") for o in oracles],
                          rotation=25, ha="right")
        rc = oracles.index("QV-DFE-RC")
        axs[1].annotate("0.0% in all\nfour settings", xy=(rc, 0.6), xytext=(rc - 0.25, 13), ha="center",
                        fontsize=6.3, color=INK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5))
        axs[1].axhline(ALPHA * 100, color=INK, lw=0.7)
        axs[1].set_ylabel("wrong verdicts (%)")
        axs[1].set_title("(b) device-calibrated noise (IBM snapshots)", loc="left")
        axs[1].grid(axis="x", visible=False)
        axs[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.38), fontsize=6.0, ncol=2)
    fig.tight_layout(w_pad=1.2)
    _save(fig, "fig_robustness")


if __name__ == "__main__":
    fig_identifiability()
    fig_observability()
    fig_boundary()
    fig_cost()
    fig_scaling()
    fig_robustness()
