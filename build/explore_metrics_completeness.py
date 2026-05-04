"""
explore_metrics_completeness.py — four-metric chart showing
annual return, Sharpe, Sortino, Calmar across the campaign with
explicit visual distinction of data completeness.

For each metric panel:
  ●  filled circle      = valid run, metric recorded
  ×  red X at value     = invalidated run, metric recorded
  |  light tick on axis = valid run, metric NOT recorded
  ×  grey small in rug  = invalidated run, metric NOT recorded

Plus a top strip showing per-run metric coverage as a 4-row heatmap.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

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

METRICS = [
    ("validation_annual_return", "Annual return",  float(spy.validation_annual_return), "#2c7b3a"),
    ("validation_sharpe",         "Sharpe",         float(spy.validation_sharpe),        "#2563eb"),
    ("validation_sortino",        "Sortino",        float(spy.validation_sortino),       "#1f4e79"),
    ("validation_calmar",         "Calmar",         float(spy.validation_calmar),        "#5b2c6f"),
]

# Sort all runs (so x-axis is meaningful)
all_runs = sorted(df.run_id.unique().tolist())

# ---------------------------------------------------------------------------
# Figure layout: top strip (2u) + 4 metric panels (4u each)
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(15, 18))
gs = fig.add_gridspec(18, 1, hspace=0.7)
ax_strip = fig.add_subplot(gs[0:2, 0])
metric_axes = [
    fig.add_subplot(gs[2:6, 0],   sharex=ax_strip),
    fig.add_subplot(gs[6:10, 0],  sharex=ax_strip),
    fig.add_subplot(gs[10:14, 0], sharex=ax_strip),
    fig.add_subplot(gs[14:18, 0], sharex=ax_strip),
]

# ---------------------------------------------------------------------------
# Top strip: per-run × per-metric coverage heatmap
# ---------------------------------------------------------------------------
runs_sorted = df.sort_values("run_id")
mat = np.full((4, len(runs_sorted)), 0.0)  # 0=missing, 1=valid+recorded, 2=invalid+recorded
for j, (col, _, _, _) in enumerate(METRICS):
    has = runs_sorted[col].notna().values
    invalid = (runs_sorted.removed == True).values
    mat[j] = np.where(~has, 0,
              np.where(invalid, 2, 1))

# Custom colormap via per-cell scatter: blocks
xpos = runs_sorted.run_id.values
for j in range(4):
    for i, rv in enumerate(mat[j]):
        if rv == 1:
            ax_strip.scatter(xpos[i], j, marker="s", s=42,
                             color=METRICS[j][3], alpha=0.9, edgecolor="none")
        elif rv == 2:
            ax_strip.scatter(xpos[i], j, marker="x", s=44,
                             color="#c0392b", alpha=0.9, linewidths=1.6)
        # rv == 0: leave blank (missing)

ax_strip.set_yticks(range(4))
ax_strip.set_yticklabels([m[1] for m in METRICS], fontsize=10)
ax_strip.set_ylim(-0.6, 3.6)
ax_strip.set_title("Per-run metric coverage map  "
                   "(■ recorded valid · × recorded invalidated · blank = not recorded)",
                   fontsize=11)
ax_strip.grid(True, axis="y", alpha=0.2, ls="--", lw=0.4)
ax_strip.spines["left"].set_visible(False)
ax_strip.tick_params(left=False)
plt.setp(ax_strip.get_xticklabels(), visible=False)

# ---------------------------------------------------------------------------
# Metric panels
# ---------------------------------------------------------------------------
for ax, (col, name, spy_v, color) in zip(metric_axes, METRICS):
    sub_has = df[df[col].notna()].copy().sort_values("run_id")
    sub_no  = df[df[col].isna()].copy().sort_values("run_id")

    valid_has   = sub_has[sub_has.removed == False]
    invalid_has = sub_has[sub_has.removed == True]
    valid_no    = sub_no[sub_no.removed == False]
    invalid_no  = sub_no[sub_no.removed == True]

    valid_has = valid_has.copy()
    valid_has["rb"] = valid_has[col].cummax()

    ymin = 0
    ymax = sub_has[col].max() * 1.10 if len(sub_has) else 1.0
    if name == "Annual return":
        ymin = sub_has[col].min() * 1.10 if (sub_has[col].min() < 0) else 0
        ymax = sub_has[col].max() * 1.10
    rug_y = ymin + 0.025 * (ymax - ymin)

    # ---- valid + not recorded: light tick on x-axis (above rug) ----
    if len(valid_no):
        tick_y = ymin + 0.005 * (ymax - ymin)
        ax.scatter(valid_no.run_id, [tick_y] * len(valid_no), marker="|",
                   s=180, color="#bbbbbb", linewidths=1.2,
                   label=f"Valid, not recorded (n={len(valid_no)})", zorder=2)

    # ---- invalid + not recorded: grey small × in rug ----
    if len(invalid_no):
        ax.scatter(invalid_no.run_id, [rug_y] * len(invalid_no), marker="x",
                   s=55, color="#888888", alpha=0.85, linewidths=1.2,
                   label=f"Invalidated, not recorded (n={len(invalid_no)})",
                   zorder=2)

    # ---- valid + recorded: filled circle ----
    if len(valid_has):
        ax.scatter(valid_has.run_id, valid_has[col], s=32, color=color,
                   alpha=0.85, edgecolor="white", linewidth=0.4,
                   label=f"Valid, recorded (n={len(valid_has)})", zorder=4)

    # ---- invalid + recorded: red × at value ----
    if len(invalid_has):
        ax.scatter(invalid_has.run_id, invalid_has[col], s=85, marker="x",
                   color="#c0392b", alpha=0.85, linewidths=1.6,
                   label=f"Invalidated, recorded (n={len(invalid_has)})",
                   zorder=3)

    # ---- running best over valid+recorded ----
    if len(valid_has):
        ax.step(valid_has.run_id, valid_has.rb, where="post", color=color,
                linewidth=2.0, alpha=0.85,
                label="Running best (valid)", zorder=5)

    # ---- SPY baseline ----
    if not np.isnan(spy_v):
        ax.axhline(spy_v, ls=":", color="#e67e22", linewidth=1.4,
                   label=f"SPY ({spy_v:.3f})", zorder=1)

    val_max = valid_has[col].max() if len(valid_has) else float("nan")
    inv_max = invalid_has[col].max() if len(invalid_has) else float("nan")
    inv_max_text = f"  invalidated max={inv_max:.2f}" if len(invalid_has) else ""
    miss_v = len(valid_no)
    miss_i = len(invalid_no)

    ax.set_ylabel(f"Validation {name}")
    ax.set_title(
        f"{name}  —  valid max={val_max:.3g}{inv_max_text}  |  "
        f"missing on {miss_v + miss_i}/{len(df)} runs "
        f"({miss_v} valid + {miss_i} invalidated)",
        fontsize=11,
    )
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95, ncol=2)
    ax.grid(True, alpha=0.25, ls="--", lw=0.5)
    ax.set_ylim(ymin, ymax)
    if name == "Annual return":
        ax.axhline(0, color="black", lw=0.6, alpha=0.6)

metric_axes[-1].set_xlabel("Experiment run_id")

# Shaded epoch bands across all panels
for ax in [ax_strip] + metric_axes:
    ax.axvspan(4, 11,  color="#888888", alpha=0.06, zorder=0)
    ax.axvspan(74, 113, color="#c0392b", alpha=0.07, zorder=0)

fig.suptitle(
    "Validation metrics across the 929-run campaign with explicit "
    "data-completeness encoding\n"
    f"({len(df)} TSV rows; ~{929 - len(df)} runs absent from this curated subset)",
    fontsize=12.5, y=0.997,
)

for ext in ("pdf", "png"):
    plt.savefig(os.path.join(OUT_DIR, f"fig_metrics_completeness.{ext}"),
                dpi=180, bbox_inches="tight")
plt.close()
print(f"Saved fig_metrics_completeness.{{pdf,png}}")
print()

# Print coverage summary
print("=== Per-metric coverage summary ===")
print(f"{'Metric':<22}{'Valid+rec':>10}{'Inv+rec':>10}{'Valid+miss':>12}{'Inv+miss':>10}")
for col, name, _, _ in METRICS:
    has = df[col].notna()
    invalid = df.removed == True
    print(f"{name:<22}"
          f"{((has) & (~invalid)).sum():>10}"
          f"{((has) & (invalid)).sum():>10}"
          f"{((~has) & (~invalid)).sum():>12}"
          f"{((~has) & (invalid)).sum():>10}")
