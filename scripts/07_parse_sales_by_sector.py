# -*- coding: utf-8 -*-
"""Parse electricity sales by consumption type (فروش انرژی برق به تفکیک نوع مصرف).

Source: manual-data/tarefe/forush_energy_by_sector_1378plus.xlsx — a single
table (sheet "28") covering 1378–1398, million kWh, with columns
  سال | خانگی | عمومی | سایر مصارف | صنعتی | کشاورزی | روشنایی معابر | جمع
(source document recorded in manual-data/PROVENANCE.md).

Output: electricity/data/sources/electricity_sales_by_sector.csv
  year, residential_gwh, public_gwh, other_gwh, industrial_gwh,
  agriculture_gwh, street_lighting_gwh, total_gwh
The row sum is asserted against the printed جمع column to 0.1%.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import MANUAL, write_tidy, log  # noqa: E402

XLSX = os.path.join(MANUAL, "tarefe", "forush_energy_by_sector_1378plus.xlsx")
COLS = ["year", "residential_gwh", "public_gwh", "other_gwh",
        "industrial_gwh", "agriculture_gwh", "street_lighting_gwh",
        "total_gwh"]


def main():
    raw = pd.ExcelFile(XLSX).parse(0, header=None)
    body = raw[pd.to_numeric(raw[0], errors="coerce").between(1300, 1500)]
    df = body.iloc[:, :8].copy()
    df.columns = COLS
    df = df.apply(pd.to_numeric, errors="coerce")
    df["year"] = df["year"].astype(int)

    parts = df[COLS[1:-1]].sum(axis=1)
    rel = ((parts - df.total_gwh).abs() / df.total_gwh)
    assert (rel < 1e-3).all(), f"row sums off by up to {rel.max():.2%}"
    assert df.year.is_monotonic_increasing and df.year.diff().dropna().eq(1).all()

    out = write_tidy(df, "electricity_sales_by_sector.csv", sort_by="year")
    log(f"wrote {out}: {df.year.min()}–{df.year.max()} "
        f"({len(df)} years; row sums match the printed totals)")


if __name__ == "__main__":
    main()
