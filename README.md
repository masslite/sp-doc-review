# Auto-Research §4.3 figure pack

This bundle contains everything we built in our session: the
chart-generation scripts, the renders (PDF + PNG), the editorial
revision document for the body section + appendix, and the data file
they were generated from.

## Folder layout

```
data/
  auto_research_clean.tsv      curated 118-row subset of the 929-run
                               campaign (TSV = tab-separated values).
                               this is the only data file used by the
                               scripts.

build/
  *.py                         chart generators, one per analysis
  *.pdf, *.png                 the rendered figures
```

## Scripts (in build/)

| Script | What it produces |
|--------|------------------|
| `architecture_search_charts.py` | the four §4.3 figures driven by the campaign log-law (campaign_loglaw, 2d_heatmap, integer_opt, simulation_compare) |
| `explore_metrics.py` | first 3-panel overview (Sharpe / Sortino / Calmar) across the campaign |
| `explore_metrics_late.py` | three-panel diagnostic per metric — top: standard running-best, mid: running-best excl. outlier, bot: zoomed late-campaign view |
| `explore_calmar_late.py` | Calmar-only late-campaign diagnostic (shows the 5.011 outlier vs the 670-690 cluster) |
| `explore_metrics_unified.py` | three-panel chart with the rule "any removed=TRUE run is invalid for ALL metrics" — uses an X rug on the bottom for invalidations without recorded value on that metric |
| `explore_metrics_completeness.py` | four-metric completeness chart (annual return / Sharpe / Sortino / Calmar) with explicit data-completeness states |
| `explore_metrics_strict.py` | strict-rule diagnostic — anything with Calmar > 2.05 OR Sortino > 2.5 OR Sharpe > 1.9 marked invalid; legends on each panel |
| `explore_metrics_combined.py` | single 4:3 chart with all metrics overlaid |
| `explore_metrics_stacked.py` | **the final stacked chart** — three panels (Annual return / Sharpe / Calmar) with strict invalidation rule, recorded-only data, holdout overlay, anchored power-law fit, new-best circles |
| `render.py` | builds `architecture_revision.pdf` — the editorial revision of the §4.3 body section + recommended appendix structure |

## Figures (in build/)

| File | Source script | Purpose |
|------|---------------|---------|
| `architecture_revision.pdf` | render.py | editorial: revised §4.3 body + appendix recommendation |
| `fig_metrics_stacked.{pdf,png}` | explore_metrics_stacked.py | **the headline chart** — final stacked version |
| `fig_campaign_loglaw_v2.{pdf,png}` | architecture_search_charts.py | dual-metric campaign log-law fit |
| `fig_2d_heatmap_calmar_v2.{pdf,png}` | architecture_search_charts.py | V_net heatmap (Calmar fit) |
| `fig_2d_heatmap_sortino_v2.{pdf,png}` | architecture_search_charts.py | V_net heatmap (Sortino fit) |
| `fig_integer_opt_v2.{pdf,png}` | architecture_search_charts.py | integer-constrained optimum |
| `fig_simulation_compare_v2.{pdf,png}` | architecture_search_charts.py | 24-month forward sim ($1M vs $10M) |
| `fig_explore_metrics.{pdf,png}` | explore_metrics.py | initial 3-panel overview |
| `fig_calmar_late_diag.{pdf,png}` | explore_calmar_late.py | Calmar late-campaign diagnostic |
| `fig_sharpe_late_diag.{pdf,png}` | explore_metrics_late.py | Sharpe late-campaign diagnostic |
| `fig_sortino_late_diag.{pdf,png}` | explore_metrics_late.py | Sortino late-campaign diagnostic |
| `fig_metrics_unified.{pdf,png}` | explore_metrics_unified.py | unified 'whole run is invalidated' chart |
| `fig_metrics_completeness.{pdf,png}` | explore_metrics_completeness.py | 4-metric completeness chart |
| `fig_metrics_combined.{pdf,png}` | explore_metrics_combined.py | single 4:3 combined chart |
| `fig_metrics_strict.{pdf,png}` | explore_metrics_strict.py | strict-rule diagnostic |

## Running any script

```
pip install pandas numpy scipy matplotlib reportlab fpdf2
python build/explore_metrics_stacked.py
```

Each script reads from `data/auto_research_clean.tsv` and writes its
output(s) into `build/`.

## On the data

The TSV has 118 rows out of the 929-run original campaign — a curated
subset. Run-id range 1-918, with substantial gaps (the largest being
runs 219-312, 451-504, 588-640, 705-792). To work with the full
dataset, push `auto-research-929-runs-clean.csv` from your local
download into `data/` and adjust the data path at the top of each
script.

## On the strict invalidation rule used in `fig_metrics_stacked`

A run is treated as invalid if any of the following hold:
- `removed = TRUE` in the TSV (look-ahead bias, buggy backtest, etc.)
- `validation_calmar > 2.05`
- `validation_sortino > 2.5`
- `validation_sharpe > 1.9`

This catches the DTF/CA family that survived the original `removed`
column but inherits look-ahead contamination from exp 208 (per the
diagnostic in run 374 of the original data).

## Anchored power-law fit form

The fit on each panel is:

```
y = SPY + c × (run_id − 1)^d
```

where SPY is the per-metric SPY baseline at run_id = 1 (fixed),
c and d are fitted, and d is constrained to (0, 5].

## Final running-best and fit summary

| Metric | Running best | SPY | Fit (2 sig figs) | R² |
|--------|--------------|-----|------------------|-----|
| Annual return | 31.2% (run 669, holdout) | 14.3% | y = 14% + 2.3% × (x−1)^0.31 | 0.77 |
| Sharpe | 1.42 (run 912) | 0.71 | y = 0.71 + 0.13 × (x−1)^0.28 | 0.78 |
| Calmar | 2.04 (run 912) | 0.41 | y = 0.41 + 0.034 × (x−1)^0.56 | 0.96 |
