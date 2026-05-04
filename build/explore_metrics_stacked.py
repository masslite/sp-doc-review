"""
explore_metrics_stacked.py — three vertically stacked panels:
Annual return, Sharpe, Calmar. Recorded values only (no estimation).
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

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

PANELS = [
    {
        "col":     "validation_annual_return",
        "name":    "Annual return",
        "color":   "#2c7b3a",
        "ymax":    0.40,
        "as_pct":  True,
        "spy_col": "validation_annual_return",
    },
    {
        "col":     "validation_sharpe",
        "name":    "Sharpe",
        "color":   "#2563eb",
        "ymax":    2.00,
        "as_pct":  False,
        "spy_col": "validation_sharpe",
    },
    {
        "col":     "validation_calmar",
        "name":    "Calmar",
        "color":   "#5b2c6f",
        "ymax":    2.20,
        "as_pct":  False,
        "spy_col": "validation_calmar",
    },
]

fig, axes = plt.subplots(3, 1, figsize=(13, 11), sharex=True)

for ax, p in zip(axes, PANELS):
    col      = p["col"]
    name     = p["name"]
    color    = p["color"]
    ymax     = p["ymax"]
    as_pct   = p["as_pct"]
    spy_col  = p["spy_col"]

    sub = df[df[col].notna()].sort_values("run_id").copy()
    valid   = sub[~sub.strict_invalid].copy()
    invalid = sub[sub.strict_invalid].copy()
    valid["rb"] = valid[col].cummax()

    # filled markers — valid recorded
    ax.scatter(valid.run_id, valid[col], s=36, color=color,
               alpha=0.85, edgecolor="white", linewidth=0.4,
               label=f"Valid (n={len(valid)})", zorder=4)

    # invalidated — red X clipped to ymax
    if len(invalid):
        plot_y = np.minimum(invalid[col].values, ymax - 0.005 * ymax)
        ax.scatter(invalid.run_id, plot_y, s=70, marker="x",
                   color="#c0392b", alpha=0.7, linewidths=1.4,
                   label=f"Invalidated (n={len(invalid)})", zorder=3)

    # running best
    ax.step(valid.run_id, valid["rb"], where="post", color=color,
            linewidth=2.0, alpha=0.9, label="Running best", zorder=5)

    # SPY baseline
    if pd.notna(spy[spy_col]):
        spy_v = float(spy[spy_col])
        spy_label = (f"SPY ({spy_v*100:.1f}%)" if as_pct
                     else f"SPY ({spy_v:.2f})")
        ax.axhline(spy_v, ls=":", color="#e67e22", linewidth=1.2,
                   label=spy_label, zorder=1)

    # Per-panel "running best = X" annotation above the final running-best point
    if len(valid):
        last_rb = valid.iloc[-1]
        rb_val = valid["rb"].max()
        rb_str = (f"{rb_val*100:.1f}%" if as_pct else f"{rb_val:.2f}")
        x_anno = last_rb.run_id
        ax.annotate(
            f"{name} running best = {rb_str}",
            xy=(x_anno, rb_val),
            xytext=(-110, 14), textcoords="offset points",
            fontsize=11, color=color, fontweight="bold",
            ha="left",
        )

    ax.set_ylabel(name)
    ax.set_ylim(0 if name != "Annual return" else min(0, sub[col].min() * 1.05),
                ymax)
    if as_pct:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x*100:.0f}%"))
        ax.yaxis.set_major_locator(MultipleLocator(0.10))
    ax.legend(loc="upper left", fontsize=9.5, framealpha=0.95, ncol=2)
    ax.grid(True, alpha=0.25, ls="--", lw=0.5)

axes[-1].set_xlabel("Experiment run_id")
plt.tight_layout()

for ext in ("pdf", "png"):
    plt.savefig(os.path.join(OUT_DIR, f"fig_metrics_stacked.{ext}"),
                dpi=180, bbox_inches="tight")
plt.close()
print("Saved fig_metrics_stacked.{pdf,png}")
print()

print("Running-best per metric (recorded only, valid):")
for p in PANELS:
    col, name = p["col"], p["name"]
    valid = df[~df.strict_invalid & df[col].notna()]
    if len(valid):
        idx = valid[col].idxmax()
        run = int(valid.loc[idx, "run_id"])
        nm = valid.loc[idx, "name"]
        v = valid[col].max()
        v_str = f"{v*100:.1f}%" if p["as_pct"] else f"{v:.3f}"
        print(f"  {name:14s} max = {v_str:>8s}  at run {run} ({nm[:40]})")
