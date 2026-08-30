# Electricity-deficit pipeline

Forecasting Iran's electricity deficit and the investment required to close
it. Numbered offline stages, one tidy schema, loud assertions,
deterministic outputs; every number the paper cites traces to a file under
`manual-data/`.

## Stages

| Stage | Reads | Writes |
|---|---|---|
| `01_parse_peak_history.py` | Tavanir 58-year report, peak-history table | `data/sources/tavanir_annual_peaks.csv` — 1346–1403: capacity (grid/off-grid/total), max supplied, max simultaneous demand, industry load, load factor |
| `02_parse_official_yearbooks.py` | official-statistics workbooks 1399–1404 | `data/sources/tavanir_official_yearbook_indicators.csv` — peak demand, available power at peak, losses %, imports/exports, thermal efficiency |
| `03_parse_monthly_peaks.py` | monthly peak-load sheet | `data/sources/tavanir_monthly_peaks.csv` — monthly peaks 1404-01…1405-05 |
| `04_build_deficit.py` | the three CSVs above | `results/electricity_deficit_by_year.csv`, `results/deficit_summary.json`, `results/fig_deficit_history.pdf/.png` |
| `05_parse_losses_and_efficiency.py` | 58-year indicator table | `data/sources/tavanir_losses_and_efficiency.csv` — losses (total, and transmission/distribution split where published), thermal efficiency, per-capita, consumption/generation shares |
| `06_parse_world_generation.py` | `data/raw/owid_energy.csv` (OWID/Ember, payload retained) | `data/sources/iran_vs_world_generation.csv`, `results/iran_vs_world_summary.json` |
| `07_parse_sales_by_sector.py` | sectoral sales workbook | `data/sources/electricity_sales_by_sector.csv` (1378–1398) |
| `08_forecast_deficit.py` | `results/electricity_deficit_by_year.csv` | `results/deficit_forecast.csv`, `results/deficit_forecast_summary.json`, `results/fig_deficit_forecast.*` |

Run in order: `python 01_… && python 02_… && python 03_… && python 04_…`
No network, no clock; rerunning must reproduce every output byte-for-byte.

## Definition that everything hangs on

**Peak deficit (MW) = max simultaneous demand − max supplied load** at the
annual peak. Demand is Tavanir's own «حداکثر تقاضای همزمان», which includes
the load it estimates was curtailed; supplied is what the grid met. The gap
is demand that existed and was not served — the operational face of ناترازی.

## Headline state (from `results/deficit_summary.json`)

- 1403: demand 80.1 GW vs supplied 62.5 GW → **deficit 17.6 GW (21.9%)**
- 1404: demand 77.5 GW vs available 62.6 GW → **deficit 14.9 GW (19.3%)**
  (grid basis; the two bases agree to ~0.25%, see 04's docstring)
- 1395→1403: demand grew **5.2%/yr**, supplied capability **2.3%/yr** —
  the two-and-a-half-point wedge that created the deficit
- cross-checks that came out exact: 1403 peak, official workbook (grid) 79,872 vs
  58-year table (whole country) 80,065 — difference 193 ≈ the off-grid 194;
  the monthly-peak sheet's 1404 maximum (77,497) matches the workbook (77,498±1)

## Forecast headline (results/deficit_forecast_summary.json)

Log-linear trends (demand 4.7%/yr on 1390–1404, supplied 2.0%/yr on
1395–1404), residual bootstrap, seed fixed. If both trajectories continue:
deficit **27.8 GW by 1408** (95% band 22.6–32.9) and **41.5 GW by 1412**
(35.3–46.9) — 36% of peak demand. Closing it by 1412 means ~41.5 GW of new
dependable capacity beyond the current trajectory. An ex-ante conditional
projection, not a forecast of policy, weather or war.

## Next stages (planned)

- industrial + household demand from the SCI surveys (`../manual-data/amar.org.ir`)
- cost side: متوسط بهای فروش/قیمت تمام‌شده + SATBA PPA + capex benchmarks →
  the "budget to close it" counterfactual (awaiting two user downloads)
- registration-gated official sources (projects pipeline, official demand
  forecast, energy balance) — documented as a limitation in PROVENANCE.md
