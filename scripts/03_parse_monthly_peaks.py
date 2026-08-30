# -*- coding: utf-8 -*-
"""Parse the monthly simultaneous-peak table (Tavanir, «پیک بار همزمان»).

Source: manual-data/tavanir/peak/pik_mahane_1404_1405.pdf — a single page,
two year-columns (1404 and 1405), one row per Solar Hijri month with the
peak demand in MW plus the day and time it occurred.

The extracted text interleaves the two columns; each record is
  {peak MW} / {HH:MM} / {day}{month} — with the month name shared between
the columns' rows. Records are re-attributed to years by walking months in
calendar order: the sequence restarts at فروردین for each year block and the
page footer names the year order (1404 first block, 1405 second).

Output: electricity/data/sources/tavanir_monthly_peaks.csv
  year, month_no, month, peak_mw, day, time
"""
import os
import re
import sys

import fitz
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import MANUAL, MONTHS, norm, write_tidy, log  # noqa: E402

PDF = os.path.join(MANUAL, "tavanir", "peak", "pik_mahane_1404_1405.pdf")


def main():
    text = norm(fitz.open(PDF)[0].get_text())
    # records: value / time / day+month
    pat = re.compile(r"(\d{4,6})\s*\n\s*(\d{1,2}:\d{2})\s*\n\s*(\d{1,2})(" +
                     "|".join(MONTHS) + ")")
    recs = [(int(m.group(1)), m.group(2), int(m.group(3)), m.group(4))
            for m in pat.finditer(text)]
    assert recs, "no records matched"

    # The page lists months once, with 1404's record and (where already
    # observed) 1405's record side by side; extraction yields them in document
    # order. Assign each record's month, then split into years: within one
    # year a month can appear once, so a repeated month starts the other year.
    rows, seen = [], {}
    for peak, time, day, month in recs:
        year = 1405 if month in seen else 1404
        seen[month] = True if month not in seen else seen[month]
        rows.append({"year": year, "month_no": MONTHS.index(month) + 1,
                     "month": month, "peak_mw": peak, "day": day, "time": time})
    df = pd.DataFrame(rows)

    # 1404 must be the complete 12-month year; 1405 the in-progress one.
    n1404 = (df.year == 1404).sum()
    assert n1404 == 12, f"1404 has {n1404} months"
    assert df.peak_mw.between(20000, 120000).all(), "peak out of range"
    # Known anchor: the 1404 annual maximum, 77,497 MW on 7 Mordad.
    assert df[df.year == 1404].peak_mw.max() == 77497

    out = write_tidy(df, "tavanir_monthly_peaks.csv", sort_by=["year", "month_no"])
    log(f"wrote {out}: {len(df)} months "
        f"(1404: {n1404}, 1405: {(df.year == 1405).sum()})")


if __name__ == "__main__":
    main()
