"""
explore_metrics_stacked.py — three vertically stacked panels:
Annual return, Sharpe, Calmar. Recorded values only (no estimation).
Two fits on validation running-best per panel: log and power-law.
Holdout points overlaid as lighter diamonds (no fit).
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator
from scipy.optimize import curve_fit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "auto_research_clean.tsv")
OUT_DIR = os.path.join(ROOT, "build")

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

CALMAR_THRESHOLD  = 2.05
SORTINO_THRESHOLD = 2.50
SHARPE_THRESHOLD  = 1.90

df = pd.read_csv(DATA, sep="\t")
df["removed"] = df.removed.astype(bool)
spy = df[df.run_id == 1].iloc[0]

calmar_flag  = df.validation_calmar.notna()  & (df.validation_calmar  > CALMAR_THRESHOLD)
sortino_flag = df.validation_sortino.notna() & (df.validation_sortino > SORTINO_THRESHOLD)
sharpe_flag  = df.validation_sharpe.notna()  & (df.validation_sharpe  > SHARPE_THRESHOLD)
df["strict_invalid"] = df.removed | calmar_flag | sortino_flag | sharpe_flag

# Holdout = rows whose name contains "holdout" or "sealed" (case-insensitive)
name_lc = df["name"].fillna("").str.lower()
df["is_holdout"] = name_lc.str.contains("holdout") | name_lc.str.contains("sealed")

# ---- fit helpers -----------------------------------------------------------

def log_fit(x, a, b):
    return a + b * np.log(x)


def pow_fit(x, a, b):
    """Power-law: y = a * x^b   (multiplicative; passes through (1, a))."""
    return a * np.power(x, b)


def fit_curve(xs, ys, func, p0):
    try:
        popt, _ = curve_fit(func, xs, ys, p0=p0, maxfev=20000)
        yp = func(xs, *popt)
        ss_res = float(np.sum((ys - yp) ** 2))
        ss_tot = float(np.sum((ys - ys.mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        return popt, r2
    except Exception:
        return None, None


PANELS = [
    {
        "col":         "validation_annual_return",
        "name":        "Annual return",
        "color":       "#2c7b3a",   # dark green
        "color_hold":  "#7dc28a",   # light green
        "ymax":        0.50,
        "as_pct":      True,
        "spy_col":     "validation_annual_return",
    },
    {
        "col":         "validation_sharpe",
        "name":        "Sharpe",
        "color":       "#1d4ed8",   # dark blue
        "color_hold":  "#7aaee8",   # light blue
        "ymax":        2.20,
        "as_pct":      False,
        "spy_col":     "validation_sharpe",
    },
    {
        "col":         "validation_calmar",
        "name":        "Calmar",
        "color":       "#5b2c6f",   # dark purple
        "color_hold":  "#b18ac4",   # light purple
        "ymax":        2.20,
        "as_pct":      False,
        "spy_col":     "validation_calmar",
    },
]

fig, axes = plt.subplots(3, 1, figsize=(13, 12), sharex=True)

xmax_plot = df.run_id.max()
xfit = np.linspace(2, xmax_plot + 1, 400)

# Common legend style (same boxstyle/alpha/fontsize for both legends)
LEGEND_KW = dict(
    fontsize=9,
    framealpha=0.95,
    edgecolor="#888888",
    fancybox=True,
)

for ax, p in zip(axes, PANELS):
    col          = p["col"]
    name         = p["name"]
    color        = p["color"]
    color_hold   = p["color_hold"]
    ymax         = p["ymax"]
    as_pct       = p["as_pct"]
    spy_col      = p["spy_col"]

    sub_all = df[df[col].notna()].sort_values("run_id").copy()

    val_data    = sub_all[(~sub_all.is_holdout) & (~sub_all.strict_invalid)].copy()
    val_invalid = sub_all[(~sub_all.is_holdout) & sub_all.strict_invalid].copy()
    hold_data   = sub_all[sub_all.is_holdout].copy()

    val_data["rb"] = val_data[col].cummax()

    # ---- validation: filled dark markers + running best ----
    ax.scatter(val_data.run_id, val_data[col], s=34, color=color,
               alpha=0.85, edgecolor="white", linewidth=0.4,
               label=f"Validation, recorded (n={len(val_data)})", zorder=4)
    if len(val_invalid):
        plot_y = np.minimum(val_invalid[col].values, ymax - 0.005 * ymax)
        ax.scatter(val_invalid.run_id, plot_y, s=70, marker="x",
                   color="#c0392b", alpha=0.7, linewidths=1.4,
                   label=f"Invalidated (n={len(val_invalid)})", zorder=3)
    ax.step(val_data.run_id, val_data["rb"], where="post", color=color,
            linewidth=2.0, alpha=0.9, label="Validation running best", zorder=5)

    # ---- holdout points: lighter diamonds, NO fit ----
    if len(hold_data):
        ax.scatter(hold_data.run_id, hold_data[col], s=85,
                   marker="D", facecolor=color_hold,
                   edgecolor=color, linewidth=1.0, alpha=0.95,
                   label=f"Holdout (n={len(hold_data)})", zorder=6)

    # ---- fits on validation running-best (log and power law) ----
    x = val_data.run_id.values.astype(float) + 1.0
    y = val_data["rb"].values.astype(float)

    log_popt, log_r2 = fit_curve(x, y, log_fit, [y[0], 0.1])
    pow_popt, pow_r2 = fit_curve(x, y, pow_fit, [y[0], 0.1])

    if log_popt is not None:
        a, b = log_popt
        ax.plot(xfit, log_fit(xfit, a, b), "--", color=color, linewidth=1.6,
                alpha=0.85, zorder=7, label="Log fit")
    if pow_popt is not None:
        c, d = pow_popt
        ax.plot(xfit, pow_fit(xfit, c, d), ":", color=color, linewidth=1.8,
                alpha=0.85, zorder=7, label="Power-law fit")

    # ---- SPY baseline ----
    if pd.notna(spy[spy_col]):
        spy_v = float(spy[spy_col])
        spy_label = (f"SPY ({spy_v*100:.1f}%)" if as_pct else f"SPY ({spy_v:.2f})")
        ax.axhline(spy_v, ls=":", color="#e67e22", linewidth=1.2,
                   label=spy_label, zorder=1)

    # ---- running best annotation ----
    if len(val_data):
        last_rb = val_data.iloc[-1]
        rb_val = val_data["rb"].max()
        rb_str = (f"{rb_val*100:.1f}%" if as_pct else f"{rb_val:.2f}")
        ax.annotate(
            f"{name} running best = {rb_str}",
            xy=(last_rb.run_id, rb_val),
            xytext=(-110, 14), textcoords="offset points",
            fontsize=11, color=color, fontweight="bold", ha="left",
        )

    # ---- y-axis & primary legend (top-left) ----
    ax.set_ylabel(name)
    ax.set_ylim(0 if name != "Annual return" else min(0, sub_all[col].min() * 1.05),
                ymax)
    if as_pct:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x*100:.0f}%"))
        ax.yaxis.set_major_locator(MultipleLocator(0.10))

    legend1 = ax.legend(loc="upper left", ncol=2, **LEGEND_KW)
    ax.add_artist(legend1)
    ax.grid(True, alpha=0.25, ls="--", lw=0.5)

    # ---- secondary fit legend (bottom-right), matched stylization ----
    fit_text_lines = []
    if log_popt is not None:
        a, b = log_popt
        if as_pct:
            fit_text_lines.append(
                f"Log:    y = {a*100:.1f}% + {b*100:.2f}% × ln(x+1),  R² = {log_r2:.3f}")
        else:
            fit_text_lines.append(
                f"Log:    y = {a:.3f} + {b:.3f} × ln(x+1),  R² = {log_r2:.3f}")
    if pow_popt is not None:
        c, d = pow_popt
        if as_pct:
            fit_text_lines.append(
                f"Power:  y = {c*100:.2f}% × (x+1)^{d:.3f},        R² = {pow_r2:.3f}")
        else:
            fit_text_lines.append(
                f"Power:  y = {c:.3f} × (x+1)^{d:.3f},        R² = {pow_r2:.3f}")
    if fit_text_lines:
        # Build matched stylization legend via proxy artists
        from matplotlib.lines import Line2D
        proxies = [
            Line2D([0], [0], color=color, ls="--", lw=1.6,
                   label=fit_text_lines[0]),
            Line2D([0], [0], color=color, ls=":",  lw=1.8,
                   label=fit_text_lines[1] if len(fit_text_lines) > 1 else ""),
        ]
        legend2 = ax.legend(handles=proxies, loc="lower right",
                            ncol=1, **LEGEND_KW)

axes[-1].set_xlabel("Experiment run_id")

fig.suptitle(
    "Auto-Research Performance Across Experiments",
    fontsize=18, fontweight="bold", y=1.005,
)
plt.tight_layout()

for ext in ("pdf", "png"):
    plt.savefig(os.path.join(OUT_DIR, f"fig_metrics_stacked.{ext}"),
                dpi=180, bbox_inches="tight")
plt.close()
print("Saved fig_metrics_stacked.{pdf,png}")
print()

print("Validation running-best per metric (recorded only):")
for p in PANELS:
    col, name = p["col"], p["name"]
    valid = df[~df.strict_invalid & ~df.is_holdout & df[col].notna()]
    if len(valid):
        v = valid[col].max()
        v_str = f"{v*100:.1f}%" if p["as_pct"] else f"{v:.3f}"
        print(f"  {name:14s} max = {v_str}  (n_valid={len(valid)})")

print()
print("Holdout points per metric:")
for p in PANELS:
    col, name = p["col"], p["name"]
    h = df[df.is_holdout & df[col].notna()]
    if len(h):
        v = h[col].max()
        v_str = f"{v*100:.1f}%" if p["as_pct"] else f"{v:.3f}"
        print(f"  {name:14s} n={len(h):2d}, max = {v_str}")
