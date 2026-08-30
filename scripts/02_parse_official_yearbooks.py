# -*- coding: utf-8 -*-
"""Parse Tavanir's official-statistics workbooks (آمارهای رسمی صنعت برق).

Source: manual-data/tavanir/amar-rasmi/rasmi_1399..1404.xlsx. Each workbook
carries the officially registered value of a handful of indicators for that
single year; the sheet set grew over time (1399–1402 have seven sheets,
1403–1404 fifteen, including the two that matter most here: peak demand and
generating capability at peak).

Each indicator sheet holds one value in its first numeric cell (province
tables like «مصرف برق» are summed). A dash or text in place of the number
("تلفات سال 1404 نهایی نشد") is recorded as missing, not zero.

Output: electricity/data/sources/tavanir_official_yearbook_indicators.csv
  year, indicator, value, unit
"""
import glob
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import MANUAL, write_tidy, log  # noqa: E402

DIR = os.path.join(MANUAL, "tavanir", "amar-rasmi")

# sheet name (normalised) -> (indicator id, unit). Persian sheet names appear
# from 1400 on; 1399 used transliterations, mapped here to the same ids.
SHEETS = {
    "حداکثر تقاضای برق در پیک": ("peak_demand_mw", "MW"),
    "توان تولید برق در اوج بار": ("available_power_at_peak_mw", "MW"),
    # «مصرف برق» is a province table whose company subtotals double-count;
    # left out until the table is parsed properly rather than shipped wrong.
    "تلفات برق": ("losses_pct", "percent"),
    "واردات": ("imports_gwh", "GWh"),
    "Varedat": ("imports_gwh", "GWh"),
    "صادرات": ("exports_gwh", "GWh"),
    "Saderat": ("exports_gwh", "GWh"),
    "راندمان کل نیروگاه ها": ("thermal_efficiency_pct", "percent"),
}


def first_number(df: pd.DataFrame):
    """First parseable number in the sheet body (skipping the title rows)."""
    for _, row in df.iterrows():
        for v in row:
            if isinstance(v, (int, float)) and not pd.isna(v):
                return float(v)
            if isinstance(v, str):
                s = v.strip().replace("/", ".").replace(",", "")
                if re.fullmatch(r"\d+(\.\d+)?", s):
                    return float(s)
    return None


def province_total(df: pd.DataFrame):
    """Sum the numeric value column of a province table (مصرف برق)."""
    nums = pd.to_numeric(df.iloc[:, -1], errors="coerce")
    vals = nums.dropna()
    return float(vals.sum()) if len(vals) else None


def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(DIR, "rasmi_1???.xlsx"))):
        year = int(re.search(r"(\d{4})", os.path.basename(f)).group(1))
        xl = pd.ExcelFile(f)
        for sheet in xl.sheet_names:
            key = sheet.strip()
            if key not in SHEETS:
                continue
            ind, unit = SHEETS[key]
            df = xl.parse(sheet, header=None, skiprows=2)
            val = province_total(df) if ind == "consumption_gwh" and df.shape[1] > 2 \
                else first_number(df)
            if val is not None:
                rows.append({"year": year, "indicator": ind,
                             "value": val, "unit": unit})
            else:
                log(f"  {year}/{ind}: no value published (recorded as missing)")

    df = pd.DataFrame(rows).drop_duplicates(subset=["year", "indicator"])
    # The two headline 1404 figures, cross-checked against the workbook by hand.
    q = df.set_index(["year", "indicator"])["value"]
    assert q.get((1404, "peak_demand_mw")) == 77498
    assert q.get((1404, "available_power_at_peak_mw")) == 62577
    out = write_tidy(df, "tavanir_official_yearbook_indicators.csv", sort_by=["indicator", "year"])
    log(f"wrote {out}: {len(df)} rows, years "
        f"{df.year.min()}–{df.year.max()}, {df.indicator.nunique()} indicators")


if __name__ == "__main__":
    main()
