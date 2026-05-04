"""
explore_metrics_combined.py — single combined chart of Sharpe /
Sortino / Calmar (plus annual return) under the strict rule.

  - 4:3 aspect ratio
  - One y-axis on the left, capped to keep running-best lines visible
  - Running-best line per metric, recorded points as filled markers,
    estimated-Sharpe as hollow markers, invalidated as red X
  - Annotated arrows for Calmar initial (SPY baseline) and final value
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
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

CALMAR_THRESHOLD = 2.05
SORTINO_THRESHOLD = 2.50
SHARPE_THRESHOLD  = 1.90
SHARPE_TO_SORTINO = 0.762

df = pd.read_csv(DATA, sep="\t")
df["removed"] = df.removed.astype(bool)
spy = df[df.run_id == 1].iloc[0]

calmar_flag  = df.validation_calmar.notna()  & (df.validation_calmar  > CALMAR_THRESHOLD)
sortino_flag = df.validation_sortino.notna() & (df.validation_sortino > SORTINO_THRESHOLD)
sharpe_flag  = df.validation_sharpe.notna()  & (df.validation_sharpe  > SHARPE_THRESHOLD)
df["strict_invalid"] = df.removed | calmar_flag | sortino_flag | sharpe_flag

df["sharpe_recorded"]  = df.validation_sharpe.notna()
df["sharpe_estimated"] = (~df.sharpe_recorded) & df.validation_sortino.notna()
df["sharpe_to_plot"]   = df.validation_sharpe.fillna(df.validation_sortino * SHARPE_TO_SORTINO)

# Per-metric specs: (column, name, color, marker, marker-size, is-est-flag)
SERIES = [
    ("validation_annual_return", "Annual return", "#2c7b3a", "s", 30, None),
    ("sharpe_to_plot",           "Sharpe",        "#2563eb", "o", 30, "sharpe_estimated"),
    ("validation_sortino",       "Sortino",       "#1f4e79", "D", 26, None),
    ("validation_calmar",        "Calmar",        "#5b2c6f", "^", 32, None),
]

fig, ax = plt.subplots(figsize=(12, 9))

YMAX = 2.6  # cap so running-best lines stay visible

for col, name, color, marker, msize, est_flag in SERIES:
    sub = df[df[col].notna()].sort_values("run_id").copy()

    valid = sub[~sub.strict_invalid].copy()
    invalid = sub[sub.strict_invalid].copy()

    valid["rb"] = valid[col].cummax()
    # Map plot col → corresponding SPY column for baseline reference
    spy_col_map = {"sharpe_to_plot": "validation_sharpe"}
    spy_lookup = spy_col_map.get(col, col)
    spy_v = float(spy[spy_lookup]) if (spy_lookup in spy.index and pd.notna(spy[spy_lookup])) else None

    # split valid into recorded vs estimated (only relevant for Sharpe)
    if est_flag is not None:
        recorded_valid = valid[~valid[est_flag]]
        estimated_valid = valid[valid[est_flag]]
    else:
        recorded_valid = valid
        estimated_valid = valid.iloc[0:0]

    # valid recorded: filled marker
    ax.scatter(recorded_valid.run_id, recorded_valid[col],
               s=msize, marker=marker, color=color, alpha=0.85,
               edgecolor="white", linewidth=0.4,
               label=f"{name} (recorded, n={len(recorded_valid)})", zorder=4)

    # valid estimated: hollow marker
    if len(estimated_valid):
        ax.scatter(estimated_valid.run_id, estimated_valid[col],
                   s=msize + 6, marker=marker, facecolor="white",
                   edgecolor=color, linewidth=1.3, alpha=0.85,
                   label=f"{name} (estimated, n={len(estimated_valid)})", zorder=4)

    # invalid: red X (clip values to YMAX so they don't blow the y range)
    if len(invalid):
        plot_y = np.minimum(invalid[col].values, YMAX - 0.02)
        ax.scatter(invalid.run_id, plot_y, s=55, marker="x",
                   color="#c0392b", alpha=0.6, linewidths=1.2,
                   zorder=2)

    # running best
    ax.step(valid.run_id, valid["rb"], where="post", color=color,
            linewidth=2.0, alpha=0.85, zorder=5)

# Single combined legend entry for invalidated
ax.scatter([], [], marker="x", color="#c0392b", alpha=0.7, s=55,
           label=f"Invalidated (any metric, n={int(df.strict_invalid.sum())})")

# ---- SPY baseline horizontal lines for each metric ----
for col, name, color, marker, _msize, _ef in SERIES:
    spy_col_map = {"sharpe_to_plot": "validation_sharpe"}
    spy_lookup = spy_col_map.get(col, col)
    if spy_lookup in spy.index and pd.notna(spy[spy_lookup]):
        ax.axhline(float(spy[spy_lookup]), ls=":", color=color, linewidth=1.0,
                   alpha=0.45)

# ---- Calmar initial-value and final-value arrows ----
calmar_valid = df[df.validation_calmar.notna() & (~df.strict_invalid)].sort_values("run_id")
calmar_first = calmar_valid.iloc[0]   # spy_benchmark
calmar_last_max_idx = calmar_valid["validation_calmar"].cummax().idxmax()
# pick the FIRST run where the max is achieved
running_max = calmar_valid.validation_calmar.cummax()
peak_run = calmar_valid.run_id[running_max.idxmax()] if len(calmar_valid) else None
peak_row = calmar_valid.loc[running_max.idxmax()]

# Arrow: Calmar initial (SPY)
ax.annotate(
    f"Calmar initial (SPY): {calmar_first.validation_calmar:.2f}",
    xy=(calmar_first.run_id, calmar_first.validation_calmar),
    xytext=(80, calmar_first.validation_calmar + 0.55),
    fontsize=10, color="#5b2c6f", fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#5b2c6f", lw=1.2),
)

# Arrow: Calmar final (max under strict rule)
ax.annotate(
    f"Calmar final: {peak_row.validation_calmar:.2f}\n"
    f"({peak_row['name'][:32]},\n"
    f" run {int(peak_row.run_id)})",
    xy=(peak_row.run_id, peak_row.validation_calmar),
    xytext=(peak_row.run_id - 350, peak_row.validation_calmar + 0.30),
    fontsize=10, color="#5b2c6f", fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#5b2c6f", lw=1.2),
)

ax.set_ylim(0, YMAX)
ax.set_xlim(-15, df.run_id.max() + 15)
ax.set_xlabel("Experiment run_id")
ax.set_ylabel("Annual return  /  Sharpe  /  Sortino  /  Calmar")
ax.set_title(
    "Architecture-search campaign — Sharpe / Sortino / Calmar / Annual return\n"
    f"(strict rule: any metric exceeding its threshold marked as invalid; "
    f"y-axis capped at {YMAX})",
    fontsize=11.5, pad=10,
)
ax.grid(True, alpha=0.25, ls="--", lw=0.5)
ax.legend(loc="upper left", fontsize=9, framealpha=0.95, ncol=2)

plt.tight_layout()
for ext in ("pdf", "png"):
    plt.savefig(os.path.join(OUT_DIR, f"fig_metrics_combined.{ext}"),
                dpi=180, bbox_inches="tight")
plt.close()
print("Saved fig_metrics_combined.{pdf,png}")
print()

# Print summary
print("Running-best (recorded + estimated, valid only):")
for col, name, _, _, _, _ in SERIES:
    valid = df[~df.strict_invalid & df[col].notna()]
    if len(valid):
        run_id = int(valid.loc[valid[col].idxmax(), "run_id"])
        nm = valid.loc[valid[col].idxmax(), "name"]
        print(f"  {name:14s} max = {valid[col].max():.3f}  at run {run_id} ({nm[:40]})")
