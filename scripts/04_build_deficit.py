# -*- coding: utf-8 -*-
"""Build the annual supply–demand–deficit dataset and its headline figures.

Inputs (produced by stages 01–03 from the collected source files):
  tavanir_annual_peaks.csv    58-year peak table (capacity, supplied, demand)
  tavanir_official_yearbook_indicators.csv   officially registered single-year indicators
  tavanir_monthly_peaks.csv    monthly peaks 1404–1405

Definitions, stated once and used everywhere:
  peak deficit (MW)  = max simultaneous demand − max load actually supplied.
    Demand here is Tavanir's own «حداکثر تقاضای همزمان», which includes the
    load it estimates was curtailed; supplied is what the grid met. The gap
    is therefore the megawatts of demand that existed and were not served at
    the annual peak — the operational face of the imbalance (ناترازی).
  deficit share (%)  = deficit / demand.

1404 is appended from the official-statistics workbook (grid basis; the
58-year table for 1403 shows the whole-country basis runs ~190 MW higher,
i.e. the bases agree to ~0.25%).

Outputs:
  electricity/results/electricity_deficit_by_year.csv
  electricity/results/deficit_summary.json
  electricity/results/fig_deficit_history.pdf / .png
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import E_DATA, E_RESULTS, log  # noqa: E402

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.spines.top": False,
    "axes.spines.right": False, "pdf.fonttype": 42,
})


def cagr(v1, v0, years):
    return (v1 / v0) ** (1 / years) - 1


def main():
    peak = pd.read_csv(os.path.join(E_DATA, "tavanir_annual_peaks.csv"))
    yearbook = pd.read_csv(os.path.join(E_DATA, "tavanir_official_yearbook_indicators.csv"))

    d = peak[["year", "cap_total_mw", "supplied_max_mw", "demand_max_mw"]].copy()

    # Append 1404 from the official workbook (grid basis, see docstring).
    r = yearbook.pivot(index="year", columns="indicator", values="value")
    d = pd.concat([d, pd.DataFrame([{
        "year": 1404,
        "cap_total_mw": None,                       # not yet published
        "supplied_max_mw": r.loc[1404, "available_power_at_peak_mw"],
        "demand_max_mw": r.loc[1404, "peak_demand_mw"],
    }])], ignore_index=True)

    d["deficit_mw"] = d["demand_max_mw"] - d["supplied_max_mw"]
    d["deficit_pct"] = 100 * d["deficit_mw"] / d["demand_max_mw"]

    est = d.dropna(subset=["deficit_mw"]).reset_index(drop=True)
    out_csv = os.path.join(E_RESULTS, "electricity_deficit_by_year.csv")
    est.to_csv(out_csv, index=False, encoding="utf-8-sig",
               lineterminator="\n", float_format="%.6g")

    # ---- headline numbers -------------------------------------------------
    last = est.iloc[-1]
    y03 = est[est.year == 1403].iloc[0]
    win = est[est.year.between(1395, 1403)]
    g_dem = cagr(win.demand_max_mw.iloc[-1], win.demand_max_mw.iloc[0], 8)
    g_sup = cagr(win.supplied_max_mw.iloc[-1], win.supplied_max_mw.iloc[0], 8)
    # the deficit first exceeds 5% of demand in:
    onset = est[est.deficit_pct > 5].year.min()

    summary = {
        "definition": "deficit = max simultaneous demand - max supplied load, "
                      "at the annual peak (Tavanir 58-year table; 1404 from "
                      "the official-statistics workbook, grid basis)",
        "deficit_1403_mw": float(y03.deficit_mw),
        "deficit_1403_pct": round(float(y03.deficit_pct), 1),
        "deficit_1404_mw": float(last.deficit_mw),
        "deficit_1404_pct": round(float(last.deficit_pct), 1),
        "demand_cagr_1395_1403_pct": round(100 * g_dem, 1),
        "supplied_cagr_1395_1403_pct": round(100 * g_sup, 1),
        "deficit_onset_year": int(onset),
        "n_years": int(len(est)),
        "monthly_peaks_through": "1405-05",
    }
    with open(os.path.join(E_RESULTS, "deficit_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # ---- figure -----------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(6.5, 5.4), sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1]})
    sub = est[est.year >= 1378]
    ax1.plot(sub.year, sub.demand_max_mw / 1000, color="#c8502d", lw=1.6,
             label="max simultaneous demand")
    ax1.plot(sub.year, sub.supplied_max_mw / 1000, color="#2d5f8a", lw=1.6,
             label="max supplied load")
    ax1.fill_between(sub.year, sub.supplied_max_mw / 1000,
                     sub.demand_max_mw / 1000, color="#c8502d", alpha=.15,
                     label="unserved at peak")
    ax1.set_ylabel("GW at annual peak")
    ax1.legend(frameon=False, loc="upper left", fontsize=8)
    ax2.bar(sub.year, sub.deficit_pct, color="#c8502d", width=.75)
    ax2.set_ylabel("deficit, % of demand")
    ax2.set_xlabel("Solar Hijri year")
    fig.tight_layout(pad=.4)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(E_RESULTS, f"fig_deficit_history.{ext}"), dpi=150)

    log(f"wrote {out_csv} ({len(est)} years with a computable deficit)")
    log(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
