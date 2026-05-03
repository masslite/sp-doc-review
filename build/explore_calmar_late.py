"""
explore_calmar_late.py — focused Calmar exploration showing the late-
campaign trajectory that's masked by the run-504 outlier in the
standard running-best view.

Three panels:
  (top)    All Calmar values + standard running-best
  (mid)    Same with running-best EXCLUDING the 5.011 outlier from
           run 504 — reveals the secondary 670-690 cluster and
           late-campaign 800-918 cluster
  (bot)    Y-axis zoomed to 0-3 to show the late-campaign growth
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
SPY_C = float(spy.validation_calmar)

sub = df[df.validation_calmar.notna()].copy().sort_values("run_id")
valid = sub[sub.removed == False].copy()
invalid = sub[sub.removed == True].copy()

# Two running-best variants
valid["rb"] = valid.validation_calmar.cummax()

# Variant: exclude the single 5.011 outlier (calmar_opt_short_weight_020,
# run 504). This row sits 0.24 above the next-highest valid value (4.771)
# and is what pins the standard running-best flat from run 504 onward.
exclude_mask = ~((valid.run_id == 504) & (valid.validation_calmar > 5.0))
valid["rb_no_outlier"] = valid.validation_calmar.where(exclude_mask).cummax()

print(f"Total Calmar-populated rows: {len(sub)}")
print(f"  valid (removed=FALSE): {len(valid)}")
print(f"  invalid (removed=TRUE): {len(invalid)}")
print()
print(f"SPY Calmar: {SPY_C:.3f}")
print(f"Max valid Calmar: {valid.validation_calmar.max():.3f}  "
      f"(run {valid.loc[valid.validation_calmar.idxmax(), 'run_id']})")
print()

# Three regions of interest
regions = [
    (300, 410, "DTF/CA jump",            "#7f56b5"),
    (640, 700, "670-690 cluster",        "#a85a3a"),
    (820, 925, "Late-campaign cluster",  "#3a8a5a"),
]

fig, axes = plt.subplots(3, 1, figsize=(13, 11), sharex=True)

# ============================== TOP PANEL ===================================
ax = axes[0]
for r0, r1, lbl, color in regions:
    ax.axvspan(r0, r1, color=color, alpha=0.08, zorder=0)

ax.scatter(invalid.run_id, invalid.validation_calmar, s=70, marker="x",
           color="#888888", alpha=0.7, linewidths=1.4,
           label=f"removed=TRUE (n={len(invalid)})", zorder=2)
ax.scatter(valid.run_id, valid.validation_calmar, s=32,
           color="#5b2c6f", alpha=0.85, edgecolor="white", linewidth=0.4,
           label=f"removed=FALSE (n={len(valid)})", zorder=3)
ax.step(valid.run_id, valid.rb, where="post", color="#5b2c6f",
        linewidth=2.0, alpha=0.9,
        label="Running best (standard)", zorder=4)
ax.axhline(SPY_C, ls=":", color="#e67e22", linewidth=1.4,
           label=f"SPY ({SPY_C:.3f})", zorder=1)

# Highlight the 5.011 outlier
outlier = valid[valid.validation_calmar > 5.0]
ax.scatter(outlier.run_id, outlier.validation_calmar, s=160,
           facecolor="none", edgecolor="#c0392b", linewidth=2.0, zorder=5)
ax.annotate("OUTLIER: 5.011\n(calmar_opt_short_weight_020,\nrun 504, single point)",
            xy=(504, 5.011),
            xytext=(180, 5.4), fontsize=9, color="#c0392b",
            fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.0))

ax.set_ylabel("Validation Calmar")
ax.set_title("Standard running-best — pinned at 5.011 by single outlier from run 504",
             fontsize=11)
ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95)
ax.grid(True, alpha=0.25, ls="--", lw=0.5)

# ============================== MID PANEL ===================================
ax = axes[1]
for r0, r1, lbl, color in regions:
    ax.axvspan(r0, r1, color=color, alpha=0.08, zorder=0)

ax.scatter(invalid.run_id, invalid.validation_calmar, s=70, marker="x",
           color="#888888", alpha=0.7, linewidths=1.4, zorder=2)
ax.scatter(valid.run_id, valid.validation_calmar, s=32,
           color="#5b2c6f", alpha=0.85, edgecolor="white", linewidth=0.4,
           zorder=3)
# Hide the outlier so it doesn't visually dominate
ax.step(valid.run_id, valid.rb_no_outlier, where="post", color="#1f4e79",
        linewidth=2.4, alpha=0.95,
        label="Running best EXCLUDING run-504 outlier", zorder=4)
ax.step(valid.run_id, valid.rb, where="post", color="#5b2c6f",
        linewidth=1.2, alpha=0.4, ls="--",
        label="Running best (standard, for reference)", zorder=4)
ax.axhline(SPY_C, ls=":", color="#e67e22", linewidth=1.4,
           label=f"SPY ({SPY_C:.3f})", zorder=1)

# Annotate the 670-690 cluster max
cluster_670 = valid[(valid.run_id >= 640) & (valid.run_id <= 700)]
if len(cluster_670):
    cmax = cluster_670.loc[cluster_670.validation_calmar.idxmax()]
    ax.annotate(f"670-690 cluster max: {cmax.validation_calmar:.2f}\n"
                f"({cmax['name'][:30]}, run {int(cmax.run_id)})",
                xy=(cmax.run_id, cmax.validation_calmar),
                xytext=(cmax.run_id - 250, cmax.validation_calmar + 0.4),
                fontsize=9, color="#a85a3a",
                arrowprops=dict(arrowstyle="->", color="#a85a3a", lw=0.8))

ax.set_ylabel("Validation Calmar")
ax.set_title("Running-best with 5.011 outlier excluded — reveals 670-690 cluster (gradual growth to 4.77)",
             fontsize=11)
ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95)
ax.grid(True, alpha=0.25, ls="--", lw=0.5)
ax.set_ylim(0, 5.5)

# ============================== BOT PANEL ===================================
ax = axes[2]
for r0, r1, lbl, color in regions:
    ax.axvspan(r0, r1, color=color, alpha=0.08, zorder=0)
    ax.text((r0+r1)/2, 2.85, lbl, ha="center", fontsize=9,
            color=color, fontweight="bold")

ax.scatter(invalid[invalid.validation_calmar < 3].run_id,
           invalid[invalid.validation_calmar < 3].validation_calmar, s=70,
           marker="x", color="#888888", alpha=0.7, linewidths=1.4,
           label="removed=TRUE", zorder=2)
ax.scatter(valid[valid.validation_calmar < 3].run_id,
           valid[valid.validation_calmar < 3].validation_calmar, s=42,
           color="#5b2c6f", alpha=0.85, edgecolor="white", linewidth=0.4,
           zorder=3)

# Late-campaign cluster: emphasize the rolling trajectory
late = valid[(valid.run_id >= 820) & (valid.validation_calmar < 3)].copy()
late = late.sort_values("run_id")
ax.plot(late.run_id, late.validation_calmar, "o-", color="#3a8a5a",
        linewidth=1.8, markersize=8, markerfacecolor="white",
        markeredgewidth=1.5, label="Late-campaign trajectory",
        zorder=5)
for _, row in late.iterrows():
    ax.annotate(f"{row.validation_calmar:.2f}",
                xy=(row.run_id, row.validation_calmar),
                xytext=(0, 8), textcoords="offset points",
                fontsize=8, color="#3a8a5a", ha="center")

ax.axhline(SPY_C, ls=":", color="#e67e22", linewidth=1.4,
           label=f"SPY ({SPY_C:.3f})", zorder=1)

ax.set_xlabel("Experiment run_id")
ax.set_ylabel("Validation Calmar")
ax.set_title("Y-axis zoomed (0-3) — late-campaign cluster shows gradual climb 1.64 → 2.34",
             fontsize=11)
ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95)
ax.grid(True, alpha=0.25, ls="--", lw=0.5)
ax.set_ylim(0, 3.0)

fig.suptitle(
    "Where late-campaign Calmar growth is hiding\n"
    f"({len(sub)} Calmar-populated rows in TSV; "
    f"~{929 - len(df)} runs absent — many additional points likely exist in raw data)",
    fontsize=12, y=1.01,
)
plt.tight_layout()
for ext in ("pdf", "png"):
    plt.savefig(os.path.join(OUT_DIR, f"fig_calmar_late_diag.{ext}"),
                dpi=180, bbox_inches="tight")
plt.close()
print(f"Saved fig_calmar_late_diag.{{pdf,png}}")

# Print regional summaries
print("\n=== Regional Calmar summary (valid only) ===")
for r0, r1, lbl, _ in regions:
    region = valid[(valid.run_id >= r0) & (valid.run_id <= r1)]
    if len(region):
        print(f"  {lbl} (run {r0}-{r1}): "
              f"n={len(region)}, "
              f"min={region.validation_calmar.min():.3f}, "
              f"max={region.validation_calmar.max():.3f}, "
              f"runs with Calmar>{1.5}: "
              f"{(region.validation_calmar > 1.5).sum()}")
