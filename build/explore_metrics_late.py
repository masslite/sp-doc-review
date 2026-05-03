"""
explore_metrics_late.py — three-panel late-campaign diagnostic for
each of Sharpe / Sortino / Calmar. Same layout as the Calmar diagnostic
but applied to all three metrics so we can see whether the "outlier
masking running best" pattern is metric-specific.

For each metric:
  (top)  All values + standard running-best
  (mid)  Running-best with the dominant outlier excluded
  (bot)  Y-axis zoomed to the late-campaign range

Removed=TRUE runs are plotted with X markers throughout.
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


def find_outlier_run(valid, col, gap_threshold=None):
    """The 'outlier' is the single highest valid point. We use it to
    define the alternative 'no-outlier' running-best."""
    if len(valid) == 0:
        return None
    return int(valid.loc[valid[col].idxmax(), "run_id"])


METRICS = [
    {
        "col": "validation_sharpe",
        "name": "Sharpe",
        "spy": float(spy.validation_sharpe),
        "color": "#2563eb",
        "regions": [
            (300, 410, "DTF/CA jump",           "#7f56b5"),
            (640, 700, "670-690 cluster",       "#a85a3a"),
            (820, 925, "Late-campaign cluster", "#3a8a5a"),
        ],
        "zoom": (0, 2.0),
    },
    {
        "col": "validation_sortino",
        "name": "Sortino",
        "spy": float(spy.validation_sortino),
        "color": "#1f4e79",
        "regions": [
            (300, 410, "DTF/CA jump",           "#7f56b5"),
            (640, 700, "670-690 cluster",       "#a85a3a"),
            (820, 925, "Late-campaign cluster", "#3a8a5a"),
        ],
        "zoom": (0, 3.0),
    },
    {
        "col": "validation_calmar",
        "name": "Calmar",
        "spy": float(spy.validation_calmar),
        "color": "#5b2c6f",
        "regions": [
            (300, 410, "DTF/CA jump",           "#7f56b5"),
            (640, 700, "670-690 cluster",       "#a85a3a"),
            (820, 925, "Late-campaign cluster", "#3a8a5a"),
        ],
        "zoom": (0, 3.0),
    },
]


def render_metric(m):
    col = m["col"]
    name = m["name"]
    spy_v = m["spy"]
    color = m["color"]
    regions = m["regions"]
    zoom = m["zoom"]

    sub = df[df[col].notna()].copy().sort_values("run_id")
    valid = sub[sub.removed == False].copy()
    invalid = sub[sub.removed == True].copy()
    valid["rb"] = valid[col].cummax()

    outlier_run = find_outlier_run(valid, col)
    outlier_val = float(valid.loc[valid[col].idxmax(), col])
    outlier_name = str(valid.loc[valid[col].idxmax(), "name"])

    # Running-best excluding the single highest valid point.
    excl_mask = valid.run_id != outlier_run
    valid["rb_no_outlier"] = valid[col].where(excl_mask).cummax()

    print(f"\n=== {name} ===")
    print(f"  total: {len(sub)}  valid: {len(valid)}  invalid: {len(invalid)}")
    print(f"  SPY: {spy_v:.3f}")
    print(f"  outlier: {outlier_val:.3f} at run {outlier_run} "
          f"({outlier_name[:40]})")
    print(f"  next-best valid: "
          f"{valid[valid.run_id != outlier_run][col].max():.3f}")

    fig, axes = plt.subplots(3, 1, figsize=(13, 11), sharex=True)

    # ---- TOP: standard running-best -----------------------------------------
    ax = axes[0]
    for r0, r1, _lbl, rcolor in regions:
        ax.axvspan(r0, r1, color=rcolor, alpha=0.08, zorder=0)

    if len(invalid):
        ax.scatter(invalid.run_id, invalid[col], s=70, marker="x",
                   color="#888888", alpha=0.7, linewidths=1.4,
                   label=f"removed=TRUE (n={len(invalid)})", zorder=2)
    ax.scatter(valid.run_id, valid[col], s=32, color=color, alpha=0.85,
               edgecolor="white", linewidth=0.4,
               label=f"removed=FALSE (n={len(valid)})", zorder=3)
    ax.step(valid.run_id, valid.rb, where="post", color=color,
            linewidth=2.0, alpha=0.9,
            label="Running best (standard)", zorder=4)
    ax.axhline(spy_v, ls=":", color="#e67e22", linewidth=1.4,
               label=f"SPY ({spy_v:.3f})", zorder=1)

    ax.scatter([outlier_run], [outlier_val], s=180, facecolor="none",
               edgecolor="#c0392b", linewidth=2.0, zorder=5)
    ax.annotate(f"OUTLIER: {outlier_val:.2f}\n"
                f"({outlier_name[:32]},\n"
                f" run {outlier_run})",
                xy=(outlier_run, outlier_val),
                xytext=(max(40, outlier_run - 250),
                        outlier_val + 0.10 * (sub[col].max() - sub[col].min())),
                fontsize=9, color="#c0392b", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.0))

    ax.set_ylabel(f"Validation {name}")
    ax.set_title(
        f"{name}: standard running-best — pinned by outlier "
        f"{outlier_val:.2f} at run {outlier_run}",
        fontsize=11,
    )
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95)
    ax.grid(True, alpha=0.25, ls="--", lw=0.5)

    # ---- MID: running-best excluding outlier --------------------------------
    ax = axes[1]
    for r0, r1, _lbl, rcolor in regions:
        ax.axvspan(r0, r1, color=rcolor, alpha=0.08, zorder=0)

    if len(invalid):
        ax.scatter(invalid.run_id, invalid[col], s=70, marker="x",
                   color="#888888", alpha=0.7, linewidths=1.4, zorder=2)
    ax.scatter(valid.run_id, valid[col], s=32, color=color, alpha=0.85,
               edgecolor="white", linewidth=0.4, zorder=3)

    ax.step(valid.run_id, valid.rb_no_outlier, where="post", color="#1f4e79",
            linewidth=2.4, alpha=0.95,
            label=f"Running best EXCLUDING run-{outlier_run} outlier",
            zorder=4)
    ax.step(valid.run_id, valid.rb, where="post", color=color,
            linewidth=1.2, alpha=0.4, ls="--",
            label="Running best (standard, ref)", zorder=4)
    ax.axhline(spy_v, ls=":", color="#e67e22", linewidth=1.4,
               label=f"SPY ({spy_v:.3f})", zorder=1)

    # Annotate next-best valid point
    rest = valid[valid.run_id != outlier_run]
    if len(rest):
        nb = rest.loc[rest[col].idxmax()]
        ax.annotate(
            f"next-best valid: {nb[col]:.2f}\n"
            f"({nb['name'][:30]}, run {int(nb.run_id)})",
            xy=(nb.run_id, nb[col]),
            xytext=(max(40, nb.run_id - 280),
                    nb[col] + 0.08 * (sub[col].max() - sub[col].min())),
            fontsize=9, color="#a85a3a",
            arrowprops=dict(arrowstyle="->", color="#a85a3a", lw=0.8),
        )

    ax.set_ylabel(f"Validation {name}")
    ax.set_title(
        f"{name}: running-best with outlier excluded — reveals secondary trajectory",
        fontsize=11,
    )
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95)
    ax.grid(True, alpha=0.25, ls="--", lw=0.5)
    ax.set_ylim(0, sub[col].max() * 1.05)

    # ---- BOT: zoomed to late-campaign range ---------------------------------
    ax = axes[2]
    for r0, r1, lbl, rcolor in regions:
        ax.axvspan(r0, r1, color=rcolor, alpha=0.08, zorder=0)
        ax.text((r0 + r1) / 2, zoom[1] * 0.94, lbl,
                ha="center", fontsize=9, color=rcolor, fontweight="bold")

    valid_z = valid[valid[col] < zoom[1]]
    invalid_z = invalid[invalid[col] < zoom[1]]
    if len(invalid_z):
        ax.scatter(invalid_z.run_id, invalid_z[col], s=70, marker="x",
                   color="#888888", alpha=0.7, linewidths=1.4,
                   label="removed=TRUE", zorder=2)
    ax.scatter(valid_z.run_id, valid_z[col], s=42, color=color,
               alpha=0.85, edgecolor="white", linewidth=0.4,
               label="removed=FALSE", zorder=3)

    # Late-campaign trajectory (run >= 820)
    late = valid[(valid.run_id >= 820) & (valid[col] < zoom[1])].copy()
    late = late.sort_values("run_id")
    if len(late) > 0:
        ax.plot(late.run_id, late[col], "o-", color="#3a8a5a",
                linewidth=1.8, markersize=8, markerfacecolor="white",
                markeredgewidth=1.5, label="Late-campaign trajectory",
                zorder=5)
        for _, row in late.iterrows():
            ax.annotate(f"{row[col]:.2f}",
                        xy=(row.run_id, row[col]),
                        xytext=(0, 8), textcoords="offset points",
                        fontsize=8, color="#3a8a5a", ha="center")

    ax.axhline(spy_v, ls=":", color="#e67e22", linewidth=1.4,
               label=f"SPY ({spy_v:.3f})", zorder=1)

    ax.set_xlabel("Experiment run_id")
    ax.set_ylabel(f"Validation {name}")
    ax.set_title(f"{name}: y-axis zoomed to {zoom} — late-campaign view",
                 fontsize=11)
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.95)
    ax.grid(True, alpha=0.25, ls="--", lw=0.5)
    ax.set_ylim(*zoom)

    fig.suptitle(
        f"{name} late-campaign diagnostic — "
        f"{len(sub)} {name}-populated rows in TSV "
        f"({len(valid)} valid + {len(invalid)} removed)",
        fontsize=12, y=1.01,
    )
    plt.tight_layout()
    out = os.path.join(OUT_DIR, f"fig_{name.lower()}_late_diag")
    for ext in ("pdf", "png"):
        plt.savefig(f"{out}.{ext}", dpi=180, bbox_inches="tight")
    plt.close()
    print(f"  Saved fig_{name.lower()}_late_diag.{{pdf,png}}")

    # Regional summary
    for r0, r1, lbl, _ in regions:
        rgn = valid[(valid.run_id >= r0) & (valid.run_id <= r1)]
        if len(rgn):
            print(f"    {lbl} (run {r0}-{r1}): "
                  f"n={len(rgn)}, "
                  f"min={rgn[col].min():.3f}, "
                  f"max={rgn[col].max():.3f}")


for m in METRICS:
    render_metric(m)
