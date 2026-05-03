"""
explore_metrics.py — exploratory view of validation Sharpe / Sortino /
Calmar across the 929-run campaign.

Plots, in one figure:
  - All experiments as markers, coloured by removed status
  - Running-best curve (only over removed=FALSE runs)
  - SPY baseline horizontal line
  - One panel per metric (Sharpe, Sortino, Calmar)
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "auto_research_clean.tsv")
OUT_DIR = os.path.join(ROOT, "build")

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

df = pd.read_csv(DATA, sep="\t")
spy = df[df.run_id == 1].iloc[0]
print(f"Rows: {len(df)} | removed=TRUE: {(df.removed == True).sum()} | "
      f"removed=FALSE: {(df.removed == False).sum()}")

METRICS = [
    ("validation_sharpe",  "Sharpe",  float(spy.validation_sharpe),  "#2563eb"),
    ("validation_sortino", "Sortino", float(spy.validation_sortino), "#1f4e79"),
    ("validation_calmar",  "Calmar",  float(spy.validation_calmar),  "#5b2c6f"),
]

fig, axes = plt.subplots(3, 1, figsize=(13, 11), sharex=True)

for ax, (col, name, spy_val, color) in zip(axes, METRICS):
    sub = df[df[col].notna()].copy().sort_values("run_id")

    valid = sub[sub.removed == False].copy()
    invalid = sub[sub.removed == True].copy()

    # Running best on the VALID runs only
    valid["running_best"] = valid[col].cummax()

    # Scatter all points
    ax.scatter(invalid.run_id, invalid[col], s=22,
               color="#bdbdbd", alpha=0.55,
               label=f"removed=TRUE (n={len(invalid)})",
               zorder=2)
    ax.scatter(valid.run_id, valid[col], s=28,
               color=color, alpha=0.85, edgecolor="white", linewidth=0.4,
               label=f"removed=FALSE (n={len(valid)})",
               zorder=3)

    # Running-best step curve
    ax.step(valid.run_id, valid.running_best, where="post",
            color=color, linewidth=2.0, alpha=0.9,
            label="Running best (valid)", zorder=4)

    # SPY baseline
    ax.axhline(spy_val, ls=":", color="#e67e22", linewidth=1.4,
               label=f"SPY ({spy_val:.3f})", zorder=1)

    # Annotations: max valid + max invalid
    if len(valid) > 0:
        max_v = valid.loc[valid[col].idxmax()]
        ax.annotate(f"max valid: {max_v[col]:.2f}\n"
                    f"({max_v['name'][:35]}, run {int(max_v.run_id)})",
                    xy=(max_v.run_id, max_v[col]),
                    xytext=(max_v.run_id - 50, max_v[col] + 0.3),
                    fontsize=8, color=color,
                    arrowprops=dict(arrowstyle="->", color=color,
                                    lw=0.6, alpha=0.6))
    if len(invalid) > 0:
        max_i = invalid.loc[invalid[col].idxmax()]
        ax.annotate(f"max invalid: {max_i[col]:.2f}",
                    xy=(max_i.run_id, max_i[col]),
                    xytext=(max_i.run_id + 30, max_i[col] - 0.3),
                    fontsize=8, color="#7a7a7a",
                    arrowprops=dict(arrowstyle="->", color="#7a7a7a",
                                    lw=0.6, alpha=0.5))

    ax.set_ylabel(f"Validation {name}")
    ax.set_title(f"{name} across the campaign — "
                 f"max valid {valid[col].max():.2f}, "
                 f"max overall {sub[col].max():.2f}",
                 fontsize=11)
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95)
    ax.grid(True, alpha=0.25, ls="--", lw=0.5)

axes[-1].set_xlabel("Experiment run_id")
fig.suptitle("929-run campaign: validation Sharpe / Sortino / Calmar",
             fontsize=13, y=1.01)
plt.tight_layout()

for ext in ("pdf", "png"):
    plt.savefig(os.path.join(OUT_DIR, f"fig_explore_metrics.{ext}"),
                dpi=180, bbox_inches="tight")
plt.close()
print(f"Saved fig_explore_metrics.{{pdf,png}}")

# Also print summary stats
print("\n=== Summary (valid + invalid) ===")
for col, name, _, _ in METRICS:
    sub = df[df[col].notna()]
    valid = sub[sub.removed == False]
    invalid = sub[sub.removed == True]
    print(f"\n{name} (validation):")
    print(f"  n_valid={len(valid)}, n_invalid={len(invalid)}")
    if len(valid) > 0:
        print(f"  valid: min={valid[col].min():.3f}  "
              f"median={valid[col].median():.3f}  "
              f"max={valid[col].max():.3f}")
    if len(invalid) > 0:
        print(f"  invalid: min={invalid[col].min():.3f}  "
              f"median={invalid[col].median():.3f}  "
              f"max={invalid[col].max():.3f}")
