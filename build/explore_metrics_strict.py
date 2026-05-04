"""
explore_metrics_strict.py — regenerated diagnostic with two changes
to the previous completeness chart:

  (a) Stricter invalidation rule: any run with validation_calmar > 2.05
      is treated as invalid in addition to removed=TRUE rows. Calmar
      values above the headline-result level are visually flagged.

  (b) Sharpe estimation: rows with Sortino but no Sharpe get an
      estimated Sharpe = 0.762 × Sortino (median empirical ratio on
      the 38 rows where both are recorded; σ = 0.069). Estimated
      Sharpe points plotted as hollow circles to distinguish from
      recorded values.

  (c) Annual return derivation from Calmar × |MaxDD|: identified, but
      only 1 candidate row in the TSV has both Calmar and MaxDD when
      annual_return is missing — so the recovered count is essentially
      zero. Surfaced as a note on the panel rather than ignored.

Visual encoding (each metric panel):
  ●  filled circle (recorded)         ✓ recorded, valid (under strict rule)
  ○  hollow circle (estimated)        ✓ estimated from a related metric
  ×  red X (recorded, invalid orig)   ✗ removed=TRUE in the data
  ▲  orange triangle (Calmar > 2.05)  ✗ flagged by strict Calmar rule
  |  light tick on x-axis             — valid run, metric not recorded
  ×  grey small in rug                — invalid run, metric not recorded
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

CALMAR_THRESHOLD = 2.05
SHARPE_TO_SORTINO = 0.762  # empirical median (std 0.069 on n=38)

# Threshold any metric whose value implies Calmar would have exceeded 2.05.
# Using the median Sortino/Calmar ratio in valid data (~1.3) and the median
# Sharpe/Sortino ratio (0.762):
#   Calmar > 2.05 implies Sortino > 2.05 / (Calmar/Sortino) ≈ 2.5
#   Sortino > 2.5 implies Sharpe  > 2.5 × 0.762        ≈ 1.9
# Anchored thresholds (rounded to be conservative — won't catch any of
# the legit late-campaign cluster which sits around Sortino 1.8-2.0):
SORTINO_THRESHOLD = 2.50
SHARPE_THRESHOLD  = 1.90

df = pd.read_csv(DATA, sep="\t")
df["removed"] = df.removed.astype(bool)
spy = df[df.run_id == 1].iloc[0]

# Strict invalidation: removed=TRUE OR any metric exceeds its threshold
calmar_flag  = df.validation_calmar.notna()  & (df.validation_calmar  > CALMAR_THRESHOLD)
sortino_flag = df.validation_sortino.notna() & (df.validation_sortino > SORTINO_THRESHOLD)
sharpe_flag  = df.validation_sharpe.notna()  & (df.validation_sharpe  > SHARPE_THRESHOLD)
df["strict_invalid"] = df.removed | calmar_flag | sortino_flag | sharpe_flag
df["calmar_flagged"]  = (~df.removed) & calmar_flag
df["sortino_flagged"] = (~df.removed) & sortino_flag & (~calmar_flag)
df["sharpe_flagged"]  = (~df.removed) & sharpe_flag  & (~calmar_flag) & (~sortino_flag)

# Estimated Sharpe for rows missing Sharpe but having Sortino
df["sharpe_recorded"] = df.validation_sharpe.notna()
df["sharpe_estimated"] = (~df.sharpe_recorded) & df.validation_sortino.notna()
df["validation_sharpe_est"] = df.validation_sortino * SHARPE_TO_SORTINO

# Estimated annual_return from Calmar × |MaxDD|
df["ar_recorded"] = df.validation_annual_return.notna()
df["ar_estimable"] = (
    (~df.ar_recorded)
    & df.validation_calmar.notna()
    & df.validation_max_drawdown.notna()
)
df["validation_annual_return_est"] = (
    df.validation_calmar * df.validation_max_drawdown.abs()
)

print(f"Rows: {len(df)}")
print(f"removed=TRUE: {df.removed.sum()}  "
      f"calmar>{CALMAR_THRESHOLD}: {df.calmar_flagged.sum()}  "
      f"sortino>{SORTINO_THRESHOLD} (no calmar): {df.sortino_flagged.sum()}  "
      f"sharpe>{SHARPE_THRESHOLD} (no calmar/sortino): {df.sharpe_flagged.sum()}  "
      f"strict_invalid total: {df.strict_invalid.sum()}")
print()
print("Calmar-flagged runs:")
print(df[df.calmar_flagged][["run_id","name","validation_sortino",
                              "validation_sharpe","validation_calmar"]].to_string())
print()
print("Sortino-flagged runs (Calmar wasn't recorded but Sortino above threshold):")
print(df[df.sortino_flagged][["run_id","name","validation_sortino",
                                "validation_sharpe","validation_calmar"]].to_string())
print()
print("Sharpe-flagged runs (above Sharpe threshold, neither Calmar nor Sortino above):")
print(df[df.sharpe_flagged][["run_id","name","validation_sortino",
                               "validation_sharpe","validation_calmar"]].to_string())
print()
print(f"Sharpe estimable from Sortino: {df.sharpe_estimated.sum()} rows")
print(f"AnnReturn estimable from Calmar×|MaxDD|: {df.ar_estimable.sum()} rows")

# Pick which Sharpe column to plot at: recorded if present, else estimated
df["sharpe_to_plot"] = df.validation_sharpe.fillna(df.validation_sharpe_est)
df["ar_to_plot"] = df.validation_annual_return.fillna(
    df.validation_annual_return_est)

METRICS = [
    ("ar_to_plot",         "validation_annual_return", "ar_recorded",       "Annual return",  float(spy.validation_annual_return), "#2c7b3a"),
    ("sharpe_to_plot",     "validation_sharpe",        "sharpe_recorded",   "Sharpe",         float(spy.validation_sharpe),        "#2563eb"),
    ("validation_sortino", "validation_sortino",       None,                "Sortino",        float(spy.validation_sortino),       "#1f4e79"),
    ("validation_calmar",  "validation_calmar",        None,                "Calmar",         float(spy.validation_calmar),        "#5b2c6f"),
]

fig = plt.figure(figsize=(15, 18))
gs = fig.add_gridspec(18, 1, hspace=0.7)
ax_strip = fig.add_subplot(gs[0:2, 0])
metric_axes = [
    fig.add_subplot(gs[2:6, 0],   sharex=ax_strip),
    fig.add_subplot(gs[6:10, 0],  sharex=ax_strip),
    fig.add_subplot(gs[10:14, 0], sharex=ax_strip),
    fig.add_subplot(gs[14:18, 0], sharex=ax_strip),
]

# ---- Top strip: coverage map (using strict_invalid + estimation flag) ----
runs_sorted = df.sort_values("run_id")
for j, (plot_col, raw_col, _rec_flag, name, _spy, color) in enumerate(METRICS):
    for _, row in runs_sorted.iterrows():
        x = row.run_id
        # Status: which kind of marker?
        recorded = pd.notna(row.get(raw_col)) if raw_col in row.index else False
        if name == "Sharpe":
            estimated = bool(row.sharpe_estimated)
        elif name == "Annual return":
            estimated = bool(row.ar_estimable)
        else:
            estimated = False

        is_inv = bool(row.strict_invalid)

        if recorded and not is_inv:
            ax_strip.scatter(x, j, marker="s", s=42, color=color,
                             alpha=0.9, edgecolor="none")
        elif recorded and is_inv:
            ax_strip.scatter(x, j, marker="x", s=44, color="#c0392b",
                             alpha=0.9, linewidths=1.6)
        elif estimated and not is_inv:
            ax_strip.scatter(x, j, marker="s", s=44, facecolor="white",
                             edgecolor=color, linewidths=1.2, alpha=0.8)
        elif estimated and is_inv:
            ax_strip.scatter(x, j, marker="x", s=30, color="#888888",
                             alpha=0.6, linewidths=1.0)
        # else blank

ax_strip.set_yticks(range(4))
ax_strip.set_yticklabels([m[3] for m in METRICS], fontsize=10)
ax_strip.set_ylim(-0.6, 3.6)
ax_strip.set_title(
    f"Per-run coverage  (■ recorded valid · □ estimated valid · "
    f"× recorded invalid (strict: removed=TRUE OR Calmar>{CALMAR_THRESHOLD}) · blank = neither)",
    fontsize=10.5,
)
ax_strip.grid(True, axis="y", alpha=0.2, ls="--", lw=0.4)
ax_strip.spines["left"].set_visible(False)
ax_strip.tick_params(left=False)
plt.setp(ax_strip.get_xticklabels(), visible=False)

# ---- Metric panels ----
for ax, (plot_col, raw_col, _rec_flag, name, spy_v, color) in zip(metric_axes, METRICS):
    sub_has_plot = df[df[plot_col].notna()].copy().sort_values("run_id")
    sub_no_plot  = df[df[plot_col].isna()].copy().sort_values("run_id")

    # categorize
    if name == "Sharpe":
        recorded_mask = df.sharpe_recorded
        estimated_mask = df.sharpe_estimated
    elif name == "Annual return":
        recorded_mask = df.ar_recorded
        estimated_mask = df.ar_estimable
    else:
        recorded_mask = df[plot_col].notna()
        estimated_mask = pd.Series([False] * len(df), index=df.index)

    valid_recorded   = df[recorded_mask & (~df.strict_invalid)]
    valid_estimated  = df[estimated_mask & (~df.strict_invalid)]
    invalid_recorded = df[recorded_mask & df.strict_invalid & (~df.calmar_flagged)]
    calmar_flag_with_value = df[df.calmar_flagged & df[plot_col].notna()]
    invalid_estimated = df[estimated_mask & df.strict_invalid]

    # also rows missing this metric entirely
    no_value = df[(~recorded_mask) & (~estimated_mask)]
    no_value_valid = no_value[~no_value.strict_invalid]
    no_value_invalid = no_value[no_value.strict_invalid]

    # running best over valid_recorded ∪ valid_estimated, sorted by run_id
    valid_all = pd.concat([valid_recorded, valid_estimated]).sort_values("run_id")
    valid_all = valid_all.copy()
    valid_all["v"] = valid_all[plot_col]
    if len(valid_all):
        valid_all["rb"] = valid_all["v"].cummax()

    ymax = max(
        sub_has_plot[plot_col].max() if len(sub_has_plot) else 1.0,
        spy_v if not np.isnan(spy_v) else 0,
    ) * 1.10
    if name == "Annual return":
        ymin = min(0, sub_has_plot[plot_col].min()) * 1.10 if len(sub_has_plot) else 0
    else:
        ymin = 0
    rug_y = ymin + 0.025 * (ymax - ymin)
    tick_y = ymin + 0.005 * (ymax - ymin)

    # rug for missing
    if len(no_value_valid):
        ax.scatter(no_value_valid.run_id, [tick_y] * len(no_value_valid),
                   marker="|", s=180, color="#bbbbbb", linewidths=1.2,
                   label=f"Valid, no data (n={len(no_value_valid)})", zorder=2)
    if len(no_value_invalid):
        ax.scatter(no_value_invalid.run_id, [rug_y] * len(no_value_invalid),
                   marker="x", s=55, color="#888888", alpha=0.85, linewidths=1.2,
                   label=f"Invalid, no data (n={len(no_value_invalid)})", zorder=2)

    # valid recorded: filled circle
    if len(valid_recorded):
        ax.scatter(valid_recorded.run_id, valid_recorded[plot_col], s=34,
                   color=color, alpha=0.85, edgecolor="white", linewidth=0.4,
                   label=f"Valid, recorded (n={len(valid_recorded)})", zorder=4)

    # valid estimated: hollow circle
    if len(valid_estimated):
        ax.scatter(valid_estimated.run_id, valid_estimated[plot_col], s=44,
                   marker="o", facecolor="white", edgecolor=color, linewidth=1.4,
                   label=f"Valid, estimated (n={len(valid_estimated)})", zorder=4)

    # invalid recorded (orig): red X
    if len(invalid_recorded):
        ax.scatter(invalid_recorded.run_id, invalid_recorded[plot_col], s=85,
                   marker="x", color="#c0392b", alpha=0.85, linewidths=1.6,
                   label=f"Invalid, recorded (n={len(invalid_recorded)})", zorder=3)

    # NEW: any-metric-flagged with value (orange triangle)
    flagged_any = df[(df.calmar_flagged | df.sortino_flagged | df.sharpe_flagged)
                     & df[plot_col].notna()]
    if len(flagged_any):
        ax.scatter(flagged_any.run_id, flagged_any[plot_col],
                   s=110, marker="^", facecolor="#f39c12", edgecolor="#7d3c0c",
                   linewidth=1.0, alpha=0.9,
                   label=f"Strict-rule flag (n={len(flagged_any)})",
                   zorder=3)

    # invalid estimated: hollow X
    if len(invalid_estimated):
        ax.scatter(invalid_estimated.run_id, invalid_estimated[plot_col], s=70,
                   marker="x", color="#aaaaaa", alpha=0.6, linewidths=1.0,
                   label=f"Invalid, estimated (n={len(invalid_estimated)})", zorder=3)

    # running best
    if len(valid_all):
        ax.step(valid_all.run_id, valid_all.rb, where="post", color=color,
                linewidth=2.0, alpha=0.85,
                label="Running best (recorded + estimated)", zorder=5)

    # SPY baseline + Calmar threshold
    if not np.isnan(spy_v):
        ax.axhline(spy_v, ls=":", color="#e67e22", linewidth=1.4,
                   label=f"SPY ({spy_v:.3f})", zorder=1)
    if name == "Calmar":
        ax.axhline(CALMAR_THRESHOLD, ls="--", color="#c0392b", linewidth=1.0,
                   alpha=0.7, label=f"Strict threshold ({CALMAR_THRESHOLD})",
                   zorder=1)

    val_max = valid_all["v"].max() if len(valid_all) else float("nan")
    note = ""
    if name == "Annual return":
        note = "  (MaxDD missing on 11 of 12 candidate rows → derivation effectively unavailable)"

    ax.set_ylabel(f"Validation {name}")
    ax.set_title(
        f"{name}  —  valid max (under strict rule + estimation): "
        f"{val_max:.3g}{note}",
        fontsize=11,
    )
    ax.legend(loc="upper left", fontsize=8.0, framealpha=0.95, ncol=2)
    ax.grid(True, alpha=0.25, ls="--", lw=0.5)
    ax.set_ylim(ymin, ymax)
    if name == "Annual return":
        ax.axhline(0, color="black", lw=0.6, alpha=0.6)

metric_axes[-1].set_xlabel("Experiment run_id")

for ax in [ax_strip] + metric_axes:
    ax.axvspan(4, 11,   color="#888888", alpha=0.06, zorder=0)
    ax.axvspan(74, 113, color="#c0392b", alpha=0.07, zorder=0)

fig.suptitle(
    f"Strict view: invalid if Calmar > {CALMAR_THRESHOLD} OR "
    f"Sortino > {SORTINO_THRESHOLD} OR Sharpe > {SHARPE_THRESHOLD}; "
    f"missing Sharpe estimated as 0.76×Sortino\n"
    f"({len(df)} TSV rows; "
    f"strict_invalid = {df.strict_invalid.sum()} runs)",
    fontsize=12.5, y=0.997,
)

for ext in ("pdf", "png"):
    plt.savefig(os.path.join(OUT_DIR, f"fig_metrics_strict.{ext}"),
                dpi=180, bbox_inches="tight")
plt.close()
print(f"Saved fig_metrics_strict.{{pdf,png}}")

# Print updated running-best maxima
print()
print("=== Running-best under strict rule (recorded + estimated) ===")
for plot_col, _raw_col, _, name, _, _ in METRICS:
    valid_runs = df[~df.strict_invalid & df[plot_col].notna()]
    if len(valid_runs):
        idx = valid_runs[plot_col].idxmax()
        row = valid_runs.loc[idx]
        is_est = ((name == "Sharpe" and row.sharpe_estimated)
                  or (name == "Annual return" and row.ar_estimable))
        print(f"  {name:14s} max = {row[plot_col]:.3f} "
              f"({'estimated' if is_est else 'recorded':9s}) "
              f"at run {int(row.run_id)} "
              f"({row['name'][:40]})")
