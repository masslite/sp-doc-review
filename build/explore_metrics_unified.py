"""
explore_metrics_unified.py — single 3-panel chart of Sharpe / Sortino /
Calmar over the campaign, where:

  - Valid points (removed=FALSE) plotted as filled circles
  - Invalidated points with a recorded value plotted as X markers at
    that value
  - Invalidated runs WITHOUT a recorded value for that metric plotted
    as small X markers in a "rug" along the bottom of the panel — so
    the timeline of invalidations is visible even when the specific
    metric wasn't populated

This implements the rule that "if a run is invalidated, the entire run
is invalidated" — including for metrics that happen to be empty for
that row.
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

# Every invalidated run in the dataset (regardless of which metric is populated)
all_invalidated_runs = sorted(df[df.removed == True].run_id.unique().tolist())

print(f"Total invalidated run_ids: {len(all_invalidated_runs)}")
print(f"Run-id range of invalidations: "
      f"{min(all_invalidated_runs)}–{max(all_invalidated_runs)}")
print()

METRICS = [
    ("validation_sharpe",  "Sharpe",  float(spy.validation_sharpe),  "#2563eb"),
    ("validation_sortino", "Sortino", float(spy.validation_sortino), "#1f4e79"),
    ("validation_calmar",  "Calmar",  float(spy.validation_calmar),  "#5b2c6f"),
]

fig, axes = plt.subplots(3, 1, figsize=(14, 11), sharex=True)

for ax, (col, name, spy_val, color) in zip(axes, METRICS):
    sub = df[df[col].notna()].copy().sort_values("run_id")
    valid = sub[sub.removed == False].copy()
    invalid_with_val = sub[sub.removed == True].copy()

    # Invalidated runs that don't have a value for THIS metric — they
    # are still invalidations of the whole run, just not visible at a
    # value on this panel.
    invalid_no_val_runs = sorted(set(all_invalidated_runs) - set(invalid_with_val.run_id.tolist()))

    valid["rb"] = valid[col].cummax()

    # Y range for this panel
    ymin = 0
    ymax = sub[col].max() * 1.10

    # Rug position (bottom of panel) for invalidated-without-value runs
    rug_y = ymin + 0.02 * (ymax - ymin)

    # ---- Plot valid points ----
    ax.scatter(valid.run_id, valid[col], s=32, color=color, alpha=0.85,
               edgecolor="white", linewidth=0.4,
               label=f"Valid runs (n={len(valid)})", zorder=4)

    # ---- Plot invalidated points (with recorded value) as X ----
    if len(invalid_with_val):
        ax.scatter(invalid_with_val.run_id, invalid_with_val[col],
                   s=85, marker="x", color="#c0392b", alpha=0.8,
                   linewidths=1.6,
                   label=f"Invalidated, recorded {name} (n={len(invalid_with_val)})",
                   zorder=3)

    # ---- Plot invalidated runs without value as small X rug at bottom ----
    if len(invalid_no_val_runs):
        ax.scatter(invalid_no_val_runs, [rug_y] * len(invalid_no_val_runs),
                   s=55, marker="x", color="#888888", alpha=0.85,
                   linewidths=1.2,
                   label=f"Invalidated, no {name} (n={len(invalid_no_val_runs)})",
                   zorder=2)

    # ---- Running best over valid only ----
    ax.step(valid.run_id, valid.rb, where="post", color=color,
            linewidth=2.0, alpha=0.85,
            label="Running best (valid only)", zorder=5)

    # ---- SPY baseline ----
    ax.axhline(spy_val, ls=":", color="#e67e22", linewidth=1.4,
               label=f"SPY ({spy_val:.3f})", zorder=1)

    # Compose summary
    val_max = valid[col].max() if len(valid) else float("nan")
    inv_max = invalid_with_val[col].max() if len(invalid_with_val) else float("nan")
    inv_max_text = f"  invalidated max={inv_max:.2f}" if len(invalid_with_val) else ""

    ax.set_ylabel(f"Validation {name}")
    ax.set_title(
        f"{name} — valid max={val_max:.2f}{inv_max_text}  |  "
        f"all 33 invalidated run_ids shown "
        f"({len(invalid_with_val)} with recorded value, "
        f"{len(invalid_no_val_runs)} as rug)",
        fontsize=10.5,
    )
    ax.legend(loc="upper left", fontsize=8.2, framealpha=0.95, ncol=1)
    ax.grid(True, alpha=0.25, ls="--", lw=0.5)
    ax.set_ylim(ymin, ymax)

axes[-1].set_xlabel("Experiment run_id")

# Shade the well-known invalidation cluster (run 74-113, look-ahead bias era)
for ax in axes:
    ax.axvspan(74, 113, color="#c0392b", alpha=0.07, zorder=0)
    # Also shade the early buggy_backtest band 4-11
    ax.axvspan(4, 11, color="#888888", alpha=0.06, zorder=0)

axes[0].text(91, axes[0].get_ylim()[1] * 0.97, "look-ahead bias era",
             ha="center", fontsize=9, color="#c0392b", fontweight="bold",
             va="top")
axes[0].text(7.5, axes[0].get_ylim()[1] * 0.91, "buggy_backtest",
             ha="center", fontsize=8, color="#666666", va="top")

fig.suptitle(
    "Sharpe / Sortino / Calmar across the 929-run campaign — "
    "X markers wherever a run is invalidated",
    fontsize=12, y=1.01,
)
plt.tight_layout()

for ext in ("pdf", "png"):
    plt.savefig(os.path.join(OUT_DIR, f"fig_metrics_unified.{ext}"),
                dpi=180, bbox_inches="tight")
plt.close()
print(f"Saved fig_metrics_unified.{{pdf,png}}")
print()

# Print which invalidated runs are NOT visible per metric
print("=== Per-metric invalidation visibility ===")
for col, name, _, _ in METRICS:
    sub = df[df[col].notna()].copy()
    invalid_with_val_runs = sub[sub.removed == True].run_id.tolist()
    invalid_no_val_runs = sorted(set(all_invalidated_runs) - set(invalid_with_val_runs))
    print(f"\n{name}:")
    print(f"  invalidated runs WITH {name} value (X at value): "
          f"n={len(invalid_with_val_runs)}")
    print(f"    runs: {invalid_with_val_runs}")
    print(f"  invalidated runs WITHOUT {name} value (X in rug): "
          f"n={len(invalid_no_val_runs)}")
    print(f"    runs: {invalid_no_val_runs}")
