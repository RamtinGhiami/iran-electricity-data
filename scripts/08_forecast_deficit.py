# -*- coding: utf-8 -*-
"""Project the peak deficit under current trends, with a bootstrap band.

Model, stated plainly (the paper will carry this paragraph):
- Peak demand and maximum supplied load are each fitted with a log-linear
  trend, demand on 1390–1404 (15 points, spanning pre- and post-deficit
  years) and supplied on 1395–1404 (the capacity-constrained era; using a
  longer window would import the pre-constraint growth rate into the
  projection of a system that no longer achieves it).
- The projection to 1412 extends both trends; deficit = demand − supplied.
- Uncertainty: residuals of each fit are resampled i.i.d. 4{,}000 times and
  added to the trend paths; the 95% band on the deficit combines both. This
  treats the trend as fixed and randomises around it — the same residual
  bootstrap the inflation paper used, honest about being a trend
  extrapolation rather than a structural model.
- This is an ex-ante conditional projection: "if the 1395–1404 supply
  trajectory and the 1390–1404 demand trajectory both continue". It is not
  a forecast of policy, weather or war.

Outputs: results/deficit_forecast.csv, results/deficit_forecast_summary.json,
         results/fig_deficit_forecast.png/.pdf
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import E_RESULTS, log  # noqa: E402

RNG = 14050607          # today's Solar Hijri date, fixed for reproducibility
H_END = 1412


def fit_loglin(df, col, y0, y1):
    sub = df[(df.year >= y0) & (df.year <= y1)].dropna(subset=[col])
    x = sub.year.to_numpy(float)
    y = np.log(sub[col].to_numpy(float))
    b, a = np.polyfit(x, y, 1)
    resid = y - (a + b * x)
    return a, b, resid, sub.year.min(), sub.year.max()


def main():
    d = pd.read_csv(os.path.join(E_RESULTS, "electricity_deficit_by_year.csv"))

    a_d, b_d, r_d, *win_d = fit_loglin(d, "demand_max_mw", 1390, 1404)
    a_s, b_s, r_s, *win_s = fit_loglin(d, "supplied_max_mw", 1395, 1404)

    years = np.arange(1405, H_END + 1)
    dem_pt = np.exp(a_d + b_d * years)
    sup_pt = np.exp(a_s + b_s * years)

    rng = np.random.default_rng(RNG)
    n = 4000
    dem_bt = np.exp(a_d + b_d * years + rng.choice(r_d, (n, len(years))))
    sup_bt = np.exp(a_s + b_s * years + rng.choice(r_s, (n, len(years))))
    def_bt = dem_bt - sup_bt

    out = pd.DataFrame({
        "year": years,
        "demand_mw": dem_pt, "supplied_mw": sup_pt,
        "deficit_mw": dem_pt - sup_pt,
        "deficit_p2_5": np.percentile(def_bt, 2.5, axis=0),
        "deficit_p50": np.percentile(def_bt, 50, axis=0),
        "deficit_p97_5": np.percentile(def_bt, 97.5, axis=0),
    })
    out["deficit_pct"] = 100 * out.deficit_mw / out.demand_mw
    out.to_csv(os.path.join(E_RESULTS, "deficit_forecast.csv"), index=False,
               encoding="utf-8-sig", lineterminator="\n", float_format="%.6g")

    y1408 = out[out.year == 1408].iloc[0]
    y1412 = out[out.year == 1412].iloc[0]
    summary = {
        "model": "log-linear trends; demand fit 1390-1404, supplied fit "
                 "1395-1404; residual bootstrap n=4000, seed 14050607",
        "demand_trend_pct_per_yr": round(100 * (np.exp(b_d) - 1), 2),
        "supplied_trend_pct_per_yr": round(100 * (np.exp(b_s) - 1), 2),
        "deficit_1408_gw": round(float(y1408.deficit_mw) / 1000, 1),
        "deficit_1408_band_gw": [round(float(y1408.deficit_p2_5) / 1000, 1),
                                 round(float(y1408.deficit_p97_5) / 1000, 1)],
        "deficit_1412_gw": round(float(y1412.deficit_mw) / 1000, 1),
        "deficit_1412_band_gw": [round(float(y1412.deficit_p2_5) / 1000, 1),
                                 round(float(y1412.deficit_p97_5) / 1000, 1)],
        "deficit_1412_pct_of_demand": round(float(y1412.deficit_pct), 1),
        "gw_of_new_dependable_capacity_to_close_by_1412":
            round(float(y1412.deficit_mw) / 1000, 1),
    }
    with open(os.path.join(E_RESULTS, "deficit_forecast_summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # ---- figure -----------------------------------------------------------
    plt.rcParams.update({"font.family": "serif", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42})
    hist = d[d.year >= 1386]
    fig, ax = plt.subplots(figsize=(6.5, 3.9))
    ax.plot(hist.year, hist.demand_max_mw / 1e3, color="#c8502d", lw=1.6,
            label="demand (observed)")
    ax.plot(hist.year, hist.supplied_max_mw / 1e3, color="#2d5f8a", lw=1.6,
            label="supplied (observed)")
    ax.plot(out.year, out.demand_mw / 1e3, color="#c8502d", lw=1.4, ls="--",
            label="demand (trend)")
    ax.plot(out.year, out.supplied_mw / 1e3, color="#2d5f8a", lw=1.4, ls="--",
            label="supplied (trend)")
    ax.fill_between(out.year, out.supplied_mw / 1e3, out.demand_mw / 1e3,
                    color="#c8502d", alpha=.12)
    lo = (out.demand_mw - out.deficit_p97_5) / 1e3
    hi = (out.demand_mw - out.deficit_p2_5) / 1e3
    ax.fill_between(out.year, lo, hi, color="#2d5f8a", alpha=.15,
                    label="95% band on the gap")
    ax.axvline(1404.5, color="#888", lw=.7, ls=":")
    ax.set_ylabel("GW at annual peak")
    ax.set_xlabel("Solar Hijri year")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left", ncols=2)
    fig.tight_layout(pad=.4)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(E_RESULTS, f"fig_deficit_forecast.{ext}"), dpi=150)

    log(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
