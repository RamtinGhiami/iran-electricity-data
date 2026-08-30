# -*- coding: utf-8 -*-
"""International mirror: Iran's electricity generation against the world.

Source: electricity/data/raw/owid_energy.csv — the Our World in Data energy
dataset (itself compiled from Ember and the Energy Institute Statistical
Review), retained as a raw payload so this stage runs offline. Ember's own
bucket refuses this network location, so OWID's GitHub mirror is the
retrieval route; the generation series is Ember's.

Produces the tidy country-year series used by the paper's comparison section
and a small JSON of headline growth numbers:
  - generation CAGR over the last decade, Iran vs world;
  - the same over the deficit era (2019- , i.e. 1398+);
  - per-capita generation, Iran vs world, latest year.

Output: data/sources/iran_vs_world_generation.csv, results/iran_vs_world_summary.json
"""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import E_DATA, E_RESULTS, write_tidy, log  # noqa: E402

RAW = os.path.join(os.path.dirname(E_DATA), "raw", "owid_energy.csv")


def cagr(series, y0, y1):
    s = series.dropna()
    if y0 not in s.index or y1 not in s.index:
        return None
    return round(100 * ((s[y1] / s[y0]) ** (1 / (y1 - y0)) - 1), 2)


def main():
    d = pd.read_csv(RAW, usecols=["country", "iso_code", "year", "population",
                                  "electricity_generation", "electricity_demand"])
    keep = d[(d.iso_code == "IRN") | (d.country == "World")].copy()
    keep["entity"] = keep.iso_code.fillna("WLD")
    tidy = keep[["entity", "year", "electricity_generation",
                 "electricity_demand", "population"]].dropna(
        subset=["electricity_generation"])
    write_tidy(tidy, "iran_vs_world_generation.csv", sort_by=["entity", "year"])

    irn = tidy[tidy.entity == "IRN"].set_index("year").electricity_generation
    wld = tidy[tidy.entity == "WLD"].set_index("year").electricity_generation
    last = int(min(irn.dropna().index.max(), wld.dropna().index.max()))
    pop = tidy[tidy.entity == "IRN"].set_index("year").population
    wpop = tidy[tidy.entity == "WLD"].set_index("year").population

    out = {
        "source": "OWID energy dataset (Ember / Energy Institute), raw payload retained",
        "latest_common_year": last,
        "iran_generation_twh_latest": round(float(irn[last]), 1),
        "gen_cagr_decade_iran_pct": cagr(irn, last - 10, last),
        "gen_cagr_decade_world_pct": cagr(wld, last - 10, last),
        "gen_cagr_deficit_era_iran_pct": cagr(irn, 2019, last),
        "gen_cagr_deficit_era_world_pct": cagr(wld, 2019, last),
        "per_capita_kwh_iran_latest": round(1e9 * float(irn[last]) / float(pop[last])),
        "per_capita_kwh_world_latest": round(1e9 * float(wld[last]) / float(wpop[last])),
    }
    with open(os.path.join(E_RESULTS, "iran_vs_world_summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    log(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
