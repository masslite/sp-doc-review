"""
explore_metrics_stacked.py — three vertically stacked panels:
Annual return, Sharpe, Calmar. Both validation and holdout data,
with log-curve fits and equation legends.
"""

import os
import re
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
SHARPE_TO_SORTINO = 0.762

df = pd.read_csv(DATA, sep="\t")
df["removed"] = df.removed.astype(bool)
spy = df[df.run_id == 1].iloc[0]

# ---- strict rule (only applied to validation data) ------------------------
calmar_flag  = df.validation_calmar.notna()  & (df.validation_calmar  > CALMAR_THRESHOLD)
sortino_flag = df.validation_sortino.notna() & (df.validation_sortino > SORTINO_THRESHOLD)
sharpe_flag  = df.validation_sharpe.notna()  & (df.validation_sharpe  > SHARPE_THRESHOLD)
df["strict_invalid"] = df.removed | calmar_flag | sortino_flag | sharpe_flag

df["sharpe_recorded"]  = df.validation_sharpe.notna()
df["sharpe_estimated"] = (~df.sharpe_recorded) & df.validation_sortino.notna()
df["sharpe_to_plot"]   = df.validation_sharpe.fillna(df.validation_sortino * SHARPE_TO_SORTINO)

# ---- identify holdout rows ------------------------------------------------
name_lc = df["name"].fillna("").str.lower()
df["is_holdout"] = (
    name_lc.str.contains("holdout")
    | name_lc.str.contains("sealed")
)
holdout_runs = df[df.is_holdout].copy()
print(f"Holdout/sealed rows identified: {len(holdout_runs)}")
print(holdout_runs[["run_id","name","validation_sortino","validation_sharpe",
                    "validation_calmar","validation_annual_return"]].to_string())
print()

# ---- log-fit helpers ------------------------------------------------------
def log_fit(x, a, b):
    return a + b * np.log(x)


def fit_running_best(df_subset, col):
    """Fit y = a + b * ln(run_id) to the running-best of `col` over df_subset."""
    sub = df_subset[df_subset[col].notna()].sort_values("run_id").copy()
    if len(sub) < 3:
        return None
    sub["rb"] = sub[col].cummax()
    x = sub.run_id.values.astype(float)
    y = sub["rb"].values.astype(float)
    # avoid log(1)=0 dominating; offset run_id by +1 so x starts at 2
    x_safe = x + 1.0
    try:
        (a, b), _ = curve_fit(log_fit, x_safe, y, p0=[y[0], 0.1], maxfev=20000)
        y_pred = log_fit(x_safe, a, b)
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        return {"a": a, "b": b, "r2": r2, "x": x, "y": y, "x_safe": x_safe}
    except Exception:
        return None


def fit_points(points_df, col):
    """Fit y = a + b * ln(run_id) to raw point values (not running-best)."""
    sub = points_df[points_df[col].notna()].sort_values("run_id").copy()
    if len(sub) < 3:
        return None
    x = sub.run_id.values.astype(float) + 1.0
    y = sub[col].values.astype(float)
    try:
        (a, b), _ = curve_fit(log_fit, x, y, p0=[y[0], 0.1], maxfev=20000)
        y_pred = log_fit(x, a, b)
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        return {"a": a, "b": b, "r2": r2}
    except Exception:
        return None


PANELS = [
    {
        "col":         "validation_annual_return",
        "name":        "Annual return",
        "color":       "#2c7b3a",   # dark green for validation
        "color_hold":  "#7dc28a",   # light green for holdout
        "ymax":        0.50,
        "as_pct":      True,
        "spy_col":     "validation_annual_return",
        "est_flag":    None,
    },
    {
        "col":         "sharpe_to_plot",
        "name":        "Sharpe",
        "color":       "#1d4ed8",   # dark blue for validation
        "color_hold":  "#7aaee8",   # light blue for holdout
        "ymax":        2.20,
        "as_pct":      False,
        "spy_col":     "validation_sharpe",
        "est_flag":    "sharpe_estimated",
    },
    {
        "col":         "validation_calmar",
        "name":        "Calmar",
        "color":       "#5b2c6f",   # dark purple for validation
        "color_hold":  "#b18ac4",   # light purple for holdout
        "ymax":        2.20,
        "as_pct":      False,
        "spy_col":     "validation_calmar",
        "est_flag":    None,
    },
]

fig, axes = plt.subplots(3, 1, figsize=(13, 12), sharex=True)

xmax = df.run_id.max()
xfit = np.linspace(2, xmax + 1, 400)

for ax, p in zip(axes, PANELS):
    col          = p["col"]
    name         = p["name"]
    color        = p["color"]
    color_hold   = p["color_hold"]
    ymax         = p["ymax"]
    as_pct       = p["as_pct"]
    spy_col      = p["spy_col"]
    est_flag     = p["est_flag"]

    sub_all = df[df[col].notna()].sort_values("run_id").copy()

    # validation = non-holdout, valid (strict rule)
    val_data = sub_all[(~sub_all.is_holdout) & (~sub_all.strict_invalid)].copy()
    val_invalid = sub_all[(~sub_all.is_holdout) & sub_all.strict_invalid].copy()

    # holdout = the named holdout rows (not subject to strict rule)
    hold_data = sub_all[sub_all.is_holdout].copy()

    val_data["rb"] = val_data[col].cummax()

    if est_flag is not None:
        val_recorded = val_data[~val_data[est_flag]]
        val_estimated = val_data[val_data[est_flag]]
    else:
        val_recorded = val_data
        val_estimated = val_data.iloc[0:0]

    # ----- validation: filled dark markers + running best -----
    ax.scatter(val_recorded.run_id, val_recorded[col], s=34, color=color,
               alpha=0.85, edgecolor="white", linewidth=0.4,
               label=f"Validation, recorded (n={len(val_recorded)})", zorder=4)
    if len(val_estimated):
        ax.scatter(val_estimated.run_id, val_estimated[col], s=40,
                   facecolor="white", edgecolor=color, linewidth=1.3, alpha=0.85,
                   label=f"Validation, estimated (n={len(val_estimated)})",
                   zorder=4)
    if len(val_invalid):
        plot_y = np.minimum(val_invalid[col].values, ymax - 0.005 * ymax)
        ax.scatter(val_invalid.run_id, plot_y, s=70, marker="x",
                   color="#c0392b", alpha=0.7, linewidths=1.4,
                   label=f"Invalidated (n={len(val_invalid)})", zorder=3)

    ax.step(val_data.run_id, val_data["rb"], where="post", color=color,
            linewidth=2.0, alpha=0.9, label="Validation running best", zorder=5)

    # ----- holdout: light markers (no strict rule applied) -----
    if len(hold_data):
        ax.scatter(hold_data.run_id, hold_data[col], s=85,
                   marker="D", color=color_hold,
                   edgecolor=color, linewidth=1.0, alpha=0.95,
                   label=f"Holdout (n={len(hold_data)})", zorder=6)

    # ----- fits -----
    val_fit  = fit_running_best(val_data, "rb" if "rb" in val_data.columns else col)
    # Re-fit on the running-best column directly:
    val_fit = None
    if len(val_data) >= 3:
        x = val_data.run_id.values.astype(float) + 1.0
        y = val_data["rb"].values.astype(float)
        try:
            (a, b), _ = curve_fit(log_fit, x, y, p0=[y[0], 0.1], maxfev=20000)
            yp = log_fit(x, a, b)
            ss_res = float(np.sum((y - yp) ** 2))
            ss_tot = float(np.sum((y - y.mean()) ** 2))
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
            val_fit = {"a": a, "b": b, "r2": r2}
        except Exception:
            val_fit = None

    hold_fit = fit_points(hold_data, col)

    if val_fit is not None:
        yfit = log_fit(xfit, val_fit["a"], val_fit["b"])
        ax.plot(xfit, yfit, "--", color=color, linewidth=1.6, alpha=0.85,
                zorder=7, label="Validation log-fit")
    if hold_fit is not None:
        yfit_h = log_fit(xfit, hold_fit["a"], hold_fit["b"])
        ax.plot(xfit, yfit_h, "--", color=color_hold, linewidth=1.8, alpha=0.95,
                zorder=7, label="Holdout log-fit")

    # ----- SPY baseline -----
    if pd.notna(spy[spy_col]):
        spy_v = float(spy[spy_col])
        spy_label = (f"SPY ({spy_v*100:.1f}%)" if as_pct else f"SPY ({spy_v:.2f})")
        ax.axhline(spy_v, ls=":", color="#e67e22", linewidth=1.2,
                   label=spy_label, zorder=1)

    # ----- running best annotation -----
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

    ax.set_ylabel(name)
    ax.set_ylim(0 if name != "Annual return" else min(0, sub_all[col].min() * 1.05),
                ymax)
    if as_pct:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x*100:.0f}%"))
        ax.yaxis.set_major_locator(MultipleLocator(0.10))
    legend1 = ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95, ncol=2)
    ax.add_artist(legend1)
    ax.grid(True, alpha=0.25, ls="--", lw=0.5)

    # ----- bottom-right secondary legend with fit equations -----
    fit_lines = []
    if val_fit is not None:
        a, b, r2 = val_fit["a"], val_fit["b"], val_fit["r2"]
        if as_pct:
            fit_lines.append(
                f"Validation: y = {a*100:.1f}% + {b*100:.2f}% × ln(x)\n"
                f"               R² = {r2:.3f}"
            )
        else:
            fit_lines.append(
                f"Validation: y = {a:.3f} + {b:.3f} × ln(x)\n"
                f"               R² = {r2:.3f}"
            )
    if hold_fit is not None:
        a, b, r2 = hold_fit["a"], hold_fit["b"], hold_fit["r2"]
        if as_pct:
            fit_lines.append(
                f"Holdout:    y = {a*100:.1f}% + {b*100:.2f}% × ln(x)\n"
                f"               R² = {r2:.3f}"
            )
        else:
            fit_lines.append(
                f"Holdout:    y = {a:.3f} + {b:.3f} × ln(x)\n"
                f"               R² = {r2:.3f}"
            )
    if fit_lines:
        text = "\n".join(fit_lines)
        ax.text(0.985, 0.04, text, transform=ax.transAxes,
                fontsize=8.5, ha="right", va="bottom",
                family="monospace",
                bbox=dict(boxstyle="round,pad=0.4",
                          facecolor="white", edgecolor="#888888", alpha=0.95))

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

print("Validation running-best per metric (recorded + estimated):")
for p in PANELS:
    col, name = p["col"], p["name"]
    valid = df[~df.strict_invalid & ~df.is_holdout & df[col].notna()]
    if len(valid):
        v = valid[col].max()
        v_str = f"{v*100:.1f}%" if p["as_pct"] else f"{v:.3f}"
        print(f"  {name:14s} max = {v_str}")

print()
print("Holdout points per metric:")
for p in PANELS:
    col, name = p["col"], p["name"]
    h = df[df.is_holdout & df[col].notna()]
    if len(h):
        v = h[col].max()
        v_str = f"{v*100:.1f}%" if p["as_pct"] else f"{v:.3f}"
        print(f"  {name:14s} n={len(h):2d}, max = {v_str}")
