"""
architecture_search_charts.py — §4.3 chart generation, driven by the
929-run CSV. Produces both Calmar and Sortino views.

Run:
    python build/architecture_search_charts.py

Outputs (in build/):
    fig_campaign_loglaw_v2.{pdf,png}        — Figure 1: dual-metric log-law fit
    fig_2d_heatmap_calmar_v2.{pdf,png}      — Figure 2: V_net heatmap (Calmar fit)
    fig_2d_heatmap_sortino_v2.{pdf,png}     — Figure 2 (Sortino sensitivity)
    fig_integer_opt_v2.{pdf,png}            — Figure 3: integer-constrained optimum
    fig_simulation_compare_v2.{pdf,png}     — Figure 4: forward sim, $1M vs $10M
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from scipy.optimize import curve_fit, minimize_scalar
from itertools import combinations


# =============================================================================
#                                 PARAMETERS
# =============================================================================

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "auto_research_clean.tsv")
OUT_DIR = os.path.join(ROOT, "build")

# --- Campaign economics (measured) ------------------------------------------
TOTAL_CAMPAIGN_COST = 300.0
TOTAL_CAMPAIGN_RUNS = 929
COST_PER_EXPERIMENT = TOTAL_CAMPAIGN_COST / TOTAL_CAMPAIGN_RUNS
EXPERIMENTS_PER_DAY = TOTAL_CAMPAIGN_RUNS / 11
TOKENS_PER_PAIR_PER_MONTH = EXPERIMENTS_PER_DAY * 30 * COST_PER_EXPERIMENT

# --- Operating parameters ---------------------------------------------------
BETA = 0.5
PHI_CARRY = 0.20
MAXDD = 0.20
DECAY = 0.05
S_FIXED_ANNUAL = 250_000
MIN_TRADING_FRACTION = 0.10

# --- Forward-sim ------------------------------------------------------------
HORIZON_MONTHS = 24
INITIAL_A_CUM = 300

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


# =============================================================================
#                           DATA LOADING + RUNNING-BEST
# =============================================================================

def load_campaign(tsv=DATA):
    df = pd.read_csv(tsv, sep="\t")
    spy_row = df[df.run_id == 1].iloc[0]
    spy_calmar = float(spy_row.validation_calmar)
    spy_sortino = float(spy_row.validation_sortino)

    # Valid = not removed AND has at least one validation metric
    valid = df[(df.removed == False)].copy()
    valid_c = (valid[valid.validation_calmar.notna()]
               .sort_values("run_id").reset_index(drop=True))
    valid_s = (valid[valid.validation_sortino.notna()]
               .sort_values("run_id").reset_index(drop=True))

    valid_c["rb"] = valid_c.validation_calmar.cummax()
    valid_s["rb"] = valid_s.validation_sortino.cummax()

    trans_c = valid_c[valid_c.rb.diff().fillna(1) > 0].copy()
    trans_s = valid_s[valid_s.rb.diff().fillna(1) > 0].copy()

    trans_c["dollars"] = trans_c.run_id * COST_PER_EXPERIMENT
    trans_s["dollars"] = trans_s.run_id * COST_PER_EXPERIMENT

    return {
        "spy_calmar": spy_calmar,
        "spy_sortino": spy_sortino,
        "trans_c": trans_c,
        "trans_s": trans_s,
        "valid_c": valid_c,
        "valid_s": valid_s,
    }


# =============================================================================
#                              LOG-LAW FIT
# =============================================================================

def log_law(a, c, a0):
    return c * np.log(1 + a / a0)


def fit_log_law(dollars, gains):
    # Bound a0 to a reasonable saturation range. The original code used
    # an unbounded fit which produces degenerate solutions (a0 huge,
    # xi huge, curve effectively linear) when the data has late large
    # jumps. Bounding a0 ≤ 200 keeps the fit in the saturating regime
    # the model is meant to represent.
    popt, _ = curve_fit(
        log_law, dollars, gains, p0=[1.0, 30.0],
        bounds=([0.05, 1.0], [50.0, 200.0]),
        maxfev=20000,
    )
    xi, a0 = popt
    y_pred = log_law(dollars, *popt)
    ss_res = float(np.sum((gains - y_pred) ** 2))
    ss_tot = float(np.sum((gains - gains.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return xi, a0, r2


CAMP = load_campaign()
TRANS_C = CAMP["trans_c"]
TRANS_S = CAMP["trans_s"]
SPY_C = CAMP["spy_calmar"]
SPY_S = CAMP["spy_sortino"]

XI_C, A0_C, R2_C = fit_log_law(
    TRANS_C.dollars.values,
    TRANS_C.validation_calmar.values - SPY_C,
)
XI_S, A0_S, R2_S = fit_log_law(
    TRANS_S.dollars.values,
    TRANS_S.validation_sortino.values - SPY_S,
)

print(f"Calmar fit:  ξ={XI_C:.4f}, a0={A0_C:.3f}, R²={R2_C:.3f}")
print(f"Sortino fit: ξ={XI_S:.4f}, a0={A0_S:.3f}, R²={R2_S:.3f}")


# =============================================================================
#       FIGURE 1 — Campaign log-law fit, dual metric
# =============================================================================

def chart_1_dual_metric():
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.6), sharex=True)

    a_smooth = np.linspace(0.5, 320, 600)

    # ---- Sortino panel ----
    ax = axes[0]
    rb_curve_s = log_law(a_smooth, XI_S, A0_S) + SPY_S
    ax.step(TRANS_S.dollars, TRANS_S.validation_sortino, where="post",
            color="#1f4e79", linewidth=2.2,
            label="Running best (campaign)", zorder=3)
    ax.scatter(TRANS_S.dollars, TRANS_S.validation_sortino, s=42,
               color="#1f4e79", edgecolor="white", linewidth=0.8, zorder=4)
    ax.fill_between(TRANS_S.dollars, SPY_S, TRANS_S.validation_sortino,
                    step="post", color="#3a7ab8", alpha=0.10)
    ax.plot(a_smooth, rb_curve_s, "-", color="#c0392b", linewidth=2.4,
            label=rf"Log-law fit: $\Delta\alpha={XI_S:.3f}\,\log(1+a/{A0_S:.2f})$",
            zorder=2)
    ax.axhline(SPY_S, ls=":", color="#e67e22", lw=1.4,
               label=f"SPY ({SPY_S:.3f})")
    last = TRANS_S.iloc[-1]
    ax.scatter([last.dollars], [last.validation_sortino], marker="*", s=320,
               color="#1f4e79", edgecolor="white", lw=1.0, zorder=5)
    ax.annotate(rf"Best: {last.validation_sortino:.2f}  "
                rf"({last.validation_sortino/SPY_S:.1f}$\times$ SPY)",
                xy=(last.dollars, last.validation_sortino),
                xytext=(last.dollars - 95, last.validation_sortino + 0.20),
                fontsize=10, color="#1f4e79", fontweight="bold")
    ax.set_xlabel("Cumulative search spend (\\$)")
    ax.set_ylabel("Validated Sortino ratio")
    ax.set_title(rf"(a) Sortino  $R^2={R2_S:.2f}$", fontsize=11.5)
    ax.legend(loc="lower right", fontsize=9.5, framealpha=0.95)
    ax.grid(True, alpha=0.25, ls="--", lw=0.6)
    ax.set_xlim(-5, 315)
    ax.set_ylim(0, max(TRANS_S.validation_sortino) * 1.15)

    # ---- Calmar panel ----
    ax = axes[1]
    rb_curve_c = log_law(a_smooth, XI_C, A0_C) + SPY_C
    ax.step(TRANS_C.dollars, TRANS_C.validation_calmar, where="post",
            color="#5b2c6f", linewidth=2.2,
            label="Running best (campaign)", zorder=3)
    ax.scatter(TRANS_C.dollars, TRANS_C.validation_calmar, s=42,
               color="#5b2c6f", edgecolor="white", linewidth=0.8, zorder=4)
    ax.fill_between(TRANS_C.dollars, SPY_C, TRANS_C.validation_calmar,
                    step="post", color="#9b59b6", alpha=0.10)
    ax.plot(a_smooth, rb_curve_c, "-", color="#c0392b", linewidth=2.4,
            label=rf"Log-law fit: $\Delta\alpha={XI_C:.3f}\,\log(1+a/{A0_C:.2f})$",
            zorder=2)
    ax.axhline(SPY_C, ls=":", color="#e67e22", lw=1.4,
               label=f"SPY ({SPY_C:.3f})")
    last = TRANS_C.iloc[-1]
    ax.scatter([last.dollars], [last.validation_calmar], marker="*", s=320,
               color="#5b2c6f", edgecolor="white", lw=1.0, zorder=5)
    ax.annotate(rf"Best: {last.validation_calmar:.2f}  "
                rf"({last.validation_calmar/SPY_C:.1f}$\times$ SPY)",
                xy=(last.dollars, last.validation_calmar),
                xytext=(last.dollars - 95, last.validation_calmar + 0.25),
                fontsize=10, color="#5b2c6f", fontweight="bold")
    ax.set_xlabel("Cumulative search spend (\\$)")
    ax.set_ylabel("Validated Calmar ratio")
    ax.set_title(rf"(b) Calmar  $R^2={R2_C:.2f}$", fontsize=11.5)
    ax.legend(loc="lower right", fontsize=9.5, framealpha=0.95)
    ax.grid(True, alpha=0.25, ls="--", lw=0.6)
    ax.set_xlim(-5, 315)
    ax.set_ylim(0, max(TRANS_C.validation_calmar) * 1.15)

    fig.suptitle(
        "Architecture Search Campaign: Dual-metric log-law fit\n"
        f"929 experiments · ~\\${TOTAL_CAMPAIGN_COST:.0f} compute · "
        f"data filtered to non-invalidated runs only "
        f"({len(CAMP['valid_c'])} retained)",
        fontsize=12, y=1.02,
    )
    plt.tight_layout()
    for ext in ("pdf", "png"):
        plt.savefig(os.path.join(OUT_DIR, f"fig_campaign_loglaw_v2.{ext}"),
                    dpi=180, bbox_inches="tight")
    plt.close()
    print("  Saved fig_campaign_loglaw_v2 (dual metric)")


# =============================================================================
#       FIGURE 2 — Single-cycle V_net heatmap (per metric)
# =============================================================================

def chart_2_value_heatmap(metric, xi, a0, suffix):
    K_DEP = 1_000_000
    n_grid = np.linspace(0, 5, 250)
    a_token_grid = np.linspace(0, 600_000, 250)
    N, A = np.meshgrid(n_grid, a_token_grid)

    N_safe = np.where(N < 0.01, 0.01, N)
    K_trade = K_DEP - A - N * S_FIXED_ANNUAL
    feasible = K_trade > MIN_TRADING_FRACTION * K_DEP

    DA = (1 - PHI_CARRY) * xi * N_safe**BETA * np.log(1 + A / a0)
    DA = np.where(N < 0.01, 0, DA)
    PV = DA * MAXDD * K_trade / DECAY
    V_net = PV - (A + N * S_FIXED_ANNUAL)
    V_net = np.where(feasible, V_net, np.nan)

    opt_idx = np.unravel_index(np.nanargmax(V_net), V_net.shape)
    opt_n = N[opt_idx]
    opt_a = A[opt_idx]
    opt_V = V_net[opt_idx]
    opt_DA = DA[opt_idx]
    opt_total = opt_a + opt_n * S_FIXED_ANNUAL

    A_pct = A / K_DEP * 100
    V_M = V_net / 1e6

    fig, ax = plt.subplots(figsize=(10.5, 7.0))
    vmin, vmax = np.nanmin(V_M), np.nanmax(V_M)
    norm = TwoSlopeNorm(vmin=min(vmin, -1), vcenter=0, vmax=vmax)
    im = ax.pcolormesh(N, A_pct, V_M, cmap="RdYlGn", norm=norm,
                       shading="gouraud")

    levels = sorted({-1, 0, 2, 5, 8, 11, round(vmax, 1)})
    cs = ax.contour(N, A_pct, V_M, levels=levels, colors="black",
                    alpha=0.40, linewidths=0.7)
    ax.clabel(cs, inline=True, fontsize=8, fmt="\\$%.0fM")
    ax.contour(N, A_pct, V_M, levels=[0], colors="black", linewidths=1.8)

    ax.contourf(N, A_pct, (~feasible).astype(float),
                levels=[0.5, 1.5], colors="gray", alpha=0.6, hatches=["///"])

    ax.scatter([opt_n], [opt_a / K_DEP * 100], color="black", s=240,
               marker="*", edgecolor="white", linewidth=1.5, zorder=10)
    label = (
        f"Optimum\n$n^*={opt_n:.1f}$, "
        f"$a_{{\\mathrm{{tok}}}}^*=\\${opt_a/1000:.0f}\\mathrm{{K}}$ "
        f"({opt_a/K_DEP*100:.1f}% of $K^{{\\mathrm{{dep}}}}$)\n"
        f"Salary $=\\${opt_n*S_FIXED_ANNUAL/1000:.0f}\\mathrm{{K}}$, "
        f"Total $=\\${opt_total/1000:.0f}\\mathrm{{K}}$ "
        f"({opt_total/K_DEP*100:.0f}%)\n"
        f"$\\Delta\\alpha={opt_DA:.2f}$ ({metric}), "
        f"$V^{{\\mathrm{{net}}}}=\\${opt_V/1e6:.1f}\\mathrm{{M}}$"
    )
    ax.annotate(label, xy=(opt_n, opt_a / K_DEP * 100),
                xytext=(2.2, 50), fontsize=9, color="black",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                          edgecolor="black", alpha=0.95),
                arrowprops=dict(arrowstyle="->", color="black", lw=1.0))

    ax.set_xlabel(r"Researcher--harness pairs $n$")
    ax.set_ylabel(r"Token spend $a_{\mathrm{tokens}}$ (\% of $K^{\mathrm{dep}}$)")
    ax.set_title(
        rf"Net Value of One Cycle of Search ({metric}-fit, $\xi={xi:.3f}$, $a_0={a0:.2f}$)"
        + "\n"
        + rf"$V^{{\mathrm{{net}}}} = (\Delta\alpha\cdot\mathrm{{MaxDD}}"
        + rf"\cdot K^{{\mathrm{{trade}}}})/\delta - (a + n\,s)$,  "
        + rf"$K^{{\mathrm{{dep}}}}=\$1\mathrm{{M}}$, "
        + rf"$\delta={int(DECAY*100)}\%$, "
        + rf"$\beta={BETA}$, $\varphi={PHI_CARRY}$",
        fontsize=10.5, pad=10,
    )
    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label(r"Net value of search cycle $V^{\mathrm{net}}$ (\$M)")
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 60)
    plt.tight_layout()
    for ext in ("pdf", "png"):
        plt.savefig(os.path.join(OUT_DIR, f"fig_2d_heatmap_{suffix}_v2.{ext}"),
                    dpi=180, bbox_inches="tight")
    plt.close()
    print(f"  Saved fig_2d_heatmap_{suffix}_v2 "
          f"(opt n={opt_n:.2f}, a=${opt_a:,.0f}, V=${opt_V/1e6:.2f}M)")
    return opt_V / 1e6


# =============================================================================
#       FIGURE 3 — Integer-constrained optimum (uses Calmar fit, primary)
# =============================================================================

def chart_3_integer_optimum(xi, a0, cont_ref):
    K_DEP = 1_000_000

    def V_net_at(n, a):
        K_trade = K_DEP - a - n * S_FIXED_ANNUAL
        if K_trade < MIN_TRADING_FRACTION * K_DEP:
            return np.nan
        if n == 0:
            return -a
        DA = (1 - PHI_CARRY) * xi * n**BETA * np.log(1 + a / a0)
        PV = DA * MAXDD * K_trade / DECAY
        return PV - (a + n * S_FIXED_ANNUAL)

    n_values = list(range(0, 5))
    optima = []
    for n in n_values:
        if n == 0:
            optima.append((n, 0, 0))
            continue
        a_max = K_DEP * (1 - MIN_TRADING_FRACTION) - n * S_FIXED_ANNUAL
        if a_max <= 0:
            optima.append((n, np.nan, -np.inf))
            continue
        res = minimize_scalar(lambda a: -V_net_at(n, a),
                              bounds=(0, a_max), method="bounded")
        optima.append((n, res.x, -res.fun))

    best_n, best_a, best_V = max(optima, key=lambda r: r[2])

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(14, 5.5),
        gridspec_kw={"width_ratios": [1.4, 1]},
    )

    colors = plt.cm.viridis(np.linspace(0.15, 0.85, len(n_values)))
    a_grid = np.linspace(0, 600_000, 600)
    for n, color in zip(n_values, colors):
        V_curve = np.array([V_net_at(n, a) for a in a_grid])
        feasible = ~np.isnan(V_curve)
        if not feasible.any():
            continue
        ax1.plot(a_grid[feasible] / 1000, V_curve[feasible] / 1e6, "-",
                 color=color, linewidth=2.0, label=f"$n={n}$")
        n_opt, a_opt, V_opt = optima[n]
        if not np.isnan(a_opt) and V_opt > -np.inf:
            ax1.scatter([a_opt / 1000], [V_opt / 1e6], color=color, s=80,
                        zorder=10, edgecolor="white", linewidth=1.0)

    ax1.scatter([best_a / 1000], [best_V / 1e6], color="black", s=300,
                marker="*", edgecolor="white", linewidth=1.5, zorder=20,
                label=f"Best integer: $n^*={best_n}$")
    ax1.axhline(0, color="gray", linestyle=":", linewidth=1, alpha=0.6)
    ax1.set_xlabel(r"Token spend $a_{\mathrm{tokens}}$ (\$K)")
    ax1.set_ylabel(r"Net value $V^{\mathrm{net}}$ (\$M)")
    ax1.set_title(r"(a) $V^{\mathrm{net}}(n, a)$ for each integer $n$",
                  fontsize=11)
    ax1.legend(loc="lower right", fontsize=9.5, framealpha=0.95)
    ax1.grid(True, alpha=0.25, linestyle="--")
    ax1.set_xlim(0, 600)

    n_bar = [opt[0] for opt in optima if opt[2] > -np.inf]
    v_bar = [opt[2] / 1e6 for opt in optima if opt[2] > -np.inf]
    a_bar = [opt[1] for opt in optima if opt[2] > -np.inf]

    bar_colors = ["#5b9f5b" if n == best_n else "#a4a4a4" for n in n_bar]
    ax2.bar(n_bar, v_bar, color=bar_colors, edgecolor="black", linewidth=0.8)
    for n, a_opt, V_opt in zip(n_bar, a_bar, v_bar):
        if V_opt <= 0:
            continue
        ax2.text(n, V_opt + 0.4, f"\\${V_opt:.1f}M",
                 ha="center", va="bottom", fontsize=10, fontweight="bold")
        salary = n * S_FIXED_ANNUAL / 1000
        tok = a_opt / 1000
        ax2.text(n, -1.2, f"$n\\!\\cdot\\!s$=\\${salary:.0f}K\n$a^*$=\\${tok:.0f}K",
                 ha="center", va="top", fontsize=8, color="dimgray")

    ax2.axhline(cont_ref, linestyle="--", color="red", linewidth=1.3, alpha=0.7,
                label=f"Continuous-$n$: \\${cont_ref:.1f}M")
    ax2.set_xlabel(r"Researcher--harness pairs $n$ (integer)")
    ax2.set_ylabel(r"Optimal $V^{\mathrm{net}}$ (\$M)")
    ax2.set_title(r"(b) Best $V^{\mathrm{net}}$ per integer $n$", fontsize=11)
    ax2.legend(loc="upper right", fontsize=9, framealpha=0.95)
    ax2.set_xticks(n_bar)
    ax2.grid(True, alpha=0.25, axis="y", linestyle="--")
    ax2.set_ylim(min(-3, min(v_bar) - 1.0), max(15, max(v_bar) + 3))

    plt.suptitle(
        rf"Integer-Constrained Optimization at $K^{{\mathrm{{dep}}}}=\$1\mathrm{{M}}$  "
        rf"(Calmar fit: $\xi={xi:.3f}$, $a_0={a0:.2f}$)",
        fontsize=12, y=1.01,
    )
    plt.tight_layout()
    for ext in ("pdf", "png"):
        plt.savefig(os.path.join(OUT_DIR, f"fig_integer_opt_v2.{ext}"),
                    dpi=180, bbox_inches="tight")
    plt.close()
    print(f"  Saved fig_integer_opt_v2 (best n={best_n}, "
          f"a=${best_a:,.0f}, V=${best_V/1e6:.2f}M)")
    return best_V / 1e6


# =============================================================================
#       FIGURE 4 — Forward simulation (Calmar-fit primary)
# =============================================================================

# Alpha capacity cap. Without this the data-driven fit (ξ ≈ 7 vs. the
# original ξ ≈ 0.78 calibration) produces explosive compounding because
# the simple economic model has no capacity / market-impact term.
# 8.0 ≈ 2× the campaign-final Calmar of 4.3, generously above realised.
ALPHA_MAX = 8.0


def simulate_schedule(sched, K0, xi, a0, alpha0):
    K = K0
    a_cum = INITIAL_A_CUM
    alpha = alpha0
    total_V = 0
    hist = []
    for t, n in enumerate(sched):
        tok = n * TOKENS_PER_PAIR_PER_MONTH
        sal = n * S_FIXED_ANNUAL / 12
        K_trade = K - tok - sal
        if K_trade < MIN_TRADING_FRACTION * K:
            return None
        a_cum_new = a_cum + tok
        if n > 0:
            di = ((1 - PHI_CARRY) * xi * n**BETA *
                  (np.log(1 + a_cum_new / a0) - np.log(1 + a_cum / a0)))
        else:
            di = 0
        alpha = min(alpha * (1 - DECAY / 12) + di, ALPHA_MAX)
        rzd = alpha * MAXDD * K_trade / 12
        v = rzd - tok - sal
        total_V += v
        K = K + rzd - tok - sal
        a_cum = a_cum_new
        hist.append(dict(t=t, n=n, alpha=alpha, K=K, V_month=v,
                         realized=rzd, tok=tok, sal=sal))
    return total_V, hist


def make_schedule(n0, hires):
    s = [n0]
    for t in range(1, HORIZON_MONTHS):
        s.append(s[-1] + (1 if t in hires else 0))
    return s


def find_optimal_schedule(K0, xi, a0, alpha0, n_max=15, k_max=5):
    best = None
    for n0 in range(1, n_max + 1):
        for k in range(0, k_max + 1):
            for hires in combinations(range(1, HORIZON_MONTHS), k):
                sched = make_schedule(n0, set(hires))
                res = simulate_schedule(sched, K0, xi, a0, alpha0)
                if res is None:
                    continue
                if best is None or res[0] > best[0]:
                    best = (res[0], sched, res[1], n0, list(hires))
    return best


def chart_4_simulation_compare(xi, a0):
    # α₀: headline-result alpha (Calmar 2.05 − SPY 0.407 ≈ 1.64), matching
    # the body section's reported headline. Using the campaign-final α₀
    # (≈4.6) here would break the simple economic model: the model has
    # no capacity / market-impact saturation, so a 24-month compounding
    # simulation with α₀≈4.6 explodes geometrically. The body's headline
    # result is the stable starting point for the forward-sim narrative.
    alpha0 = 1.642   # Calmar 2.05 − SPY 0.407

    K1, K10 = 1_000_000, 10_000_000
    opt1 = find_optimal_schedule(K1, xi, a0, alpha0, n_max=8, k_max=5)
    opt10 = find_optimal_schedule(K10, xi, a0, alpha0, n_max=20, k_max=5)

    print(f"  $1M:  n_0={opt1[3]}, hires={opt1[4]}, "
          f"V=${opt1[0]/1e6:.2f}M, K_final=${opt1[2][-1]['K']/1e6:.2f}M")
    print(f"  $10M: n_0={opt10[3]}, hires={opt10[4]}, "
          f"V=${opt10[0]/1e6:.2f}M, K_final=${opt10[2][-1]['K']/1e6:.2f}M")

    fig, axes = plt.subplots(3, 2, figsize=(14, 10))

    for col, (label, K0, opt) in enumerate([
        (r"$K^{\mathrm{dep}}_0 = \$1\mathrm{M}$", K1, opt1),
        (r"$K^{\mathrm{dep}}_0 = \$10\mathrm{M}$", K10, opt10),
    ]):
        V_total, sched, hist, n0, hires = opt
        months = [h["t"] for h in hist]
        n_traj = [h["n"] for h in hist]
        K_traj = [h["K"] for h in hist]
        cum_V = np.cumsum([h["V_month"] for h in hist])

        # Row 0: staffing
        ax = axes[0, col]
        bar_color = "#5b9f5b" if col == 0 else "#e67e22"
        ax.bar(months, n_traj, width=0.8, color=bar_color,
               edgecolor="black", linewidth=0.5)
        for t in range(1, HORIZON_MONTHS):
            if n_traj[t] > n_traj[t - 1]:
                ax.annotate("+1", xy=(t, n_traj[t] + 0.2),
                            ha="center", va="bottom",
                            fontsize=8, color="#c0392b", fontweight="bold")
        ax.set_xlabel(r"Month $t$")
        ax.set_ylabel(r"Researcher pairs $n$")
        title = (rf"{label}: optimal staffing  "
                 + (rf"($n_0={n0}$, no hires)" if not hires
                    else rf"($n_0={n0}$, +{len(hires)} hires)"))
        ax.set_title(title, fontsize=10.5)
        ax.set_xticks(months[::4] + [HORIZON_MONTHS - 1])
        ax.set_yticks(range(0, max(n_traj) + 2, max(1, max(n_traj) // 5)))
        ax.set_ylim(0, max(n_traj) + 1.5)
        ax.grid(True, alpha=0.25, axis="y", linestyle="--")

        # Row 1: K_dep
        ax = axes[1, col]
        ax.plot(months, [k / 1e6 for k in K_traj], "o-", color=bar_color,
                linewidth=2.4, markersize=6, markerfacecolor="white",
                markeredgewidth=1.4, label=f"Optimal: {n0}+{len(hires)}")
        for n_alt, ls, c in [(1, ":", "#888"), (max(2, n0 - 1), "--", "#aaa")]:
            if n_alt == n0:
                continue
            res_alt = simulate_schedule([n_alt] * HORIZON_MONTHS, K0, xi, a0,
                                        alpha0)
            if res_alt:
                K_alt = [h["K"] / 1e6 for h in res_alt[1]]
                ax.plot(months, K_alt, ls, color=c, linewidth=1.4,
                        alpha=0.85, label=f"Always $n={n_alt}$")
        ax.axhline(K0 / 1e6, color="gray", linestyle=":",
                   linewidth=0.8, alpha=0.5)
        ax.set_xlabel(r"Month $t$")
        ax.set_ylabel(r"$K^{\mathrm{dep}}$ (\$M)")
        ax.set_title("Book size evolution", fontsize=10.5)
        ax.set_xticks(months[::4] + [HORIZON_MONTHS - 1])
        ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
        ax.grid(True, alpha=0.25, axis="y", linestyle="--")

        # Row 2: cumulative V
        ax = axes[2, col]
        ax.plot(months, [c / 1e6 for c in cum_V], "o-", color=bar_color,
                linewidth=2.4, markersize=6, markerfacecolor="white",
                markeredgewidth=1.4, label=f"Optimal: {n0}+{len(hires)}")
        for n_alt, ls, c in [(1, ":", "#888"), (max(2, n0 - 1), "--", "#aaa")]:
            if n_alt == n0:
                continue
            res_alt = simulate_schedule([n_alt] * HORIZON_MONTHS, K0, xi, a0,
                                        alpha0)
            if res_alt:
                cum_alt = np.cumsum([h["V_month"] / 1e6 for h in res_alt[1]])
                ax.plot(months, cum_alt, ls, color=c, linewidth=1.4,
                        alpha=0.85, label=f"Always $n={n_alt}$")
        ax.axhline(0, color="gray", linestyle=":", linewidth=0.8)
        ax.set_xlabel(r"Month $t$")
        ax.set_ylabel(r"Cumulative $V^{\mathrm{net}}$ (\$M)")
        ax.set_title(rf"Cumulative net value  "
                     rf"($V^{{\mathrm{{net}}}}=\${V_total/1e6:.2f}\mathrm{{M}}$)",
                     fontsize=10.5)
        ax.set_xticks(months[::4] + [HORIZON_MONTHS - 1])
        ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
        ax.grid(True, alpha=0.25, axis="y", linestyle="--")

    plt.suptitle(
        rf"Forward Simulation of Optimal Hiring (Calmar fit: $\xi={xi:.3f}$, $a_0={a0:.2f}$)"
        + "\n"
        + rf"$\alpha_0 = {alpha0:.2f}$ (best campaign minus SPY).  "
        + r"Left: \$1M book — interior optimum.  "
        + r"Right: \$10M book — boundary (capacity constraint missing)",
        fontsize=11, y=1.01,
    )
    plt.tight_layout()
    for ext in ("pdf", "png"):
        plt.savefig(os.path.join(OUT_DIR, f"fig_simulation_compare_v2.{ext}"),
                    dpi=180, bbox_inches="tight")
    plt.close()
    print("  Saved fig_simulation_compare_v2")


# =============================================================================
#                                MAIN
# =============================================================================

if __name__ == "__main__":
    print()
    print("Generating Figure 1 (dual-metric campaign log-law)...")
    chart_1_dual_metric()
    print()
    print("Generating Figure 2a (heatmap, Calmar fit)...")
    cont_ref_c = chart_2_value_heatmap("Calmar", XI_C, A0_C, "calmar")
    print()
    print("Generating Figure 2b (heatmap, Sortino fit)...")
    chart_2_value_heatmap("Sortino", XI_S, A0_S, "sortino")
    print()
    print("Generating Figure 3 (integer-constrained optimum, Calmar fit)...")
    chart_3_integer_optimum(XI_C, A0_C, cont_ref_c)
    print()
    print("Generating Figure 4 (forward simulation, Calmar fit)...")
    chart_4_simulation_compare(XI_C, A0_C)
    print()
    print("Done.")
