# -*- coding: utf-8 -*-
"""Parse the 58-year peak table (Tavanir, "58 سال صنعت برق در آیینه آمار").

Source: manual-data/tavanir/long-series/58sal_sanat_bargh.pdf, the page titled
«حداکثر قدرت تولیدی، تأمین‌شده و حداکثر تقاضای همزمان» — one row per year,
1346–1403, all in megawatts.

Layout in the extracted text (5 physical lines per year):
  L0  {year}{month}{grid max generating capacity}
  L1  {off-grid capacity}
  L2  early years: {total capacity}
      later years: {total}{month}{max supplied}{month}{max simultaneous demand}
  L3  early years: {supplied}ـ   (demand not yet measured -> dash)
      later years: {industry load at peak}
  L4  early years: ـ{load factor}
      later years: {load factor}
Interludes ("متوسط رشد سالانه...", "شروع برنامه ...") are skipped.

The variants are handled by tokenising each year-block and assigning by the
count and order of (num, month, dash) tokens rather than by line position.

Output: electricity/data/sources/tavanir_annual_peaks.csv with columns
  year, cap_grid_mw, cap_offgrid_mw, cap_total_mw, supplied_max_mw,
  demand_max_mw, industry_at_peak_mw, load_factor_pct, peak_month
Missing values (early years' demand, industry) are empty cells, not zeros.
"""
import sys
import os

import fitz
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import MANUAL, tokens, write_tidy, log  # noqa: E402

PDF = os.path.join(MANUAL, "tavanir", "long-series", "58sal_sanat_bargh.pdf")
PAGE_TITLE = "ﺣﺪاﮐﺜﺮ ﻗﺪرت ﺗﻮﻟﯿﺪ"      # presentation-form glyphs as extracted


def find_page(doc):
    for i, page in enumerate(doc):
        t = page.get_text()
        if "ﺗﺄﻣﯿﻦ ﺷﺪه" in t and "ﻏﯿﺮ ﻫﻤﺮوز" in t:
            return i
    raise SystemExit("peak table page not found")


def parse(doc):
    from utils import norm
    page = find_page(doc)
    lines = [l.strip() for l in doc[page].get_text().splitlines() if l.strip()]

    # Group into per-year token streams: a block starts at a line whose first
    # token is a year immediately followed by a month name, and absorbs the
    # following lines until the next such line. Interlude lines (plan-period
    # markers and average-growth annotations) are dropped entirely — they
    # contain years and numbers that would otherwise leak into a block.
    blocks, cur = [], None
    for raw in lines:
        line = norm(raw)
        if any(w in line for w in ("متوسط", "شروع", "درصد", "علت", "اتصال")):
            continue
        toks = list(tokens(raw))
        starts_year = (toks and toks[0][0] == "year"
                       and 1346 <= toks[0][1] <= 1403
                       and len(toks) > 1 and toks[1][0] == "month")
        if starts_year:
            if cur:
                blocks.append(cur)
            # Only the leading token is the row label; a 13xx/14xx later in
            # the same line (e.g. "1352شهریور1391") is a megawatt value.
            cur = toks[:1] + [("num", float(v)) if k == "year" else (k, v)
                              for k, v in toks[1:]]
        elif cur is not None:
            # A "year" seen mid-block is really a megawatt value that happens
            # to fall in 1300–1499 (e.g. total capacity 1461 MW in 1351);
            # the year label only ever opens a block.
            cur += [("num", float(v)) if k == "year" else (k, v)
                    for k, v in toks]
    if cur:
        blocks.append(cur)

    rows = []
    for toks in blocks:
        year = toks[0][1]
        months = [v for k, v in toks if k == "month"]
        nums = [v for k, v in toks if k == "num"]
        row = {"year": year, "peak_month": months[0]}
        # Three historical layouts, distinguished by how many month names the
        # row carries (see module docstring):
        if len(months) >= 2 and len(nums) >= 7:      # 1369+: full columns
            # (supplied and demand may share a printed month, so the row can
            # carry 2 or 3 month names; the numeric order is stable.)
            row.update(cap_grid_mw=nums[0], cap_offgrid_mw=nums[1],
                       cap_total_mw=nums[2], supplied_max_mw=nums[3],
                       demand_max_mw=nums[4], industry_at_peak_mw=nums[5],
                       load_factor_pct=nums[6])
        elif len(months) == 2 and len(nums) == 6:    # a few 1370s years: no demand
            row.update(cap_grid_mw=nums[0], cap_offgrid_mw=nums[1],
                       cap_total_mw=nums[2], supplied_max_mw=nums[3],
                       demand_max_mw=None, industry_at_peak_mw=nums[4],
                       load_factor_pct=nums[5])
        elif len(months) == 1 and len(nums) >= 5:    # 1346–1368: earliest
            row.update(cap_grid_mw=nums[0], cap_offgrid_mw=nums[1],
                       cap_total_mw=nums[2], supplied_max_mw=nums[3],
                       demand_max_mw=None, industry_at_peak_mw=None,
                       load_factor_pct=nums[4])
        else:
            log(f"  [!] year {year}: unrecognised token shape "
                f"({len(nums)} nums, {len(months)} months) — skipped")
            continue
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    doc = fitz.open(PDF)
    df = parse(doc)

    # Assertions in the spirit of 09_verify: fail loudly, never silently.
    years = sorted(df["year"].tolist())
    assert years[0] == 1346 and years[-1] == 1403, f"span {years[0]}..{years[-1]}"
    missing = sorted(set(range(1346, 1404)) - set(years))
    assert not missing, f"missing years: {missing}"
    assert (df["cap_total_mw"].diff().dropna() > -6000).all(), "capacity collapse?"
    assert df.loc[df.year == 1403, "demand_max_mw"].iloc[0] == 80065
    assert df.loc[df.year == 1403, "supplied_max_mw"].iloc[0] == 62508

    out = write_tidy(df, "tavanir_annual_peaks.csv", sort_by="year")
    log(f"wrote {out}: {len(df)} years {years[0]}–{years[-1]}")
    have_demand = df["demand_max_mw"].notna().sum()
    log(f"  demand column populated for {have_demand} years")


if __name__ == "__main__":
    main()
