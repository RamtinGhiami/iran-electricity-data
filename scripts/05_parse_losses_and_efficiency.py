# -*- coding: utf-8 -*-
"""Parse the 58-year indicator table («برخی از نماگرهای مهم صنعت برق»).

Source: the same Tavanir 58-year report, the page whose columns are
  سال | تلفات شبکه (کل / انتقال و فوق‌توزیع / توزیع، درصد) | راندمان
  نیروگاه‌های حرارتی | قدرت سرانه (وات) | تولید سرانه (کیلووات‌ساعت) |
  سهم بخش‌های مصرف (خانگی/صنعتی/سایر) | سهم منابع تولید (غیرحرارتی/حرارتی)

Two layouts: 1346–1384 report total losses only (9 numbers per row);
1385–1403 add the transmission/distribution split (11 numbers).

Parsing rules learned the hard way on this report:
- a new row starts at a line holding exactly the next expected year
  (per-capita kWh values pass through the 1300–1400 range in the late 1370s
  and would otherwise be mistaken for year labels);
- footnoted cells use a dot decimal ("19.9*"), everything else the Persian
  slash — the tokeniser accepts both.

Output: electricity/data/sources/tavanir_losses_and_efficiency.csv
  year, loss_total_pct, loss_transmission_pct, loss_distribution_pct,
  thermal_efficiency_pct, capacity_per_capita_w, generation_per_capita_kwh,
  share_residential_pct, share_industrial_pct, share_other_pct,
  share_nonthermal_pct, share_thermal_pct
"""
import os
import sys

import fitz
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import MANUAL, norm, tokens, write_tidy, log  # noqa: E402

PDF = os.path.join(MANUAL, "tavanir", "long-series", "58sal_sanat_bargh.pdf")


def main():
    doc = fitz.open(PDF)
    idx = next(i for i, p in enumerate(doc)
               if "ﻧﻤﺎﮔﺮ" in p.get_text() and "ﺗﻠﻔﺎت" in p.get_text())
    lines = [norm(l.strip()) for l in doc[idx].get_text().splitlines()
             if l.strip()]

    rows, cur_year, cur_nums, expect = [], None, [], 1346
    def flush():
        nonlocal cur_year, cur_nums
        if cur_year is None:
            return
        n = cur_nums
        base = {"year": cur_year}
        if len(n) >= 11 and cur_year >= 1385:   # the split is published from 1385
            base.update(loss_total_pct=n[0], loss_transmission_pct=n[1],
                        loss_distribution_pct=n[2], thermal_efficiency_pct=n[3],
                        capacity_per_capita_w=n[4], generation_per_capita_kwh=n[5],
                        share_residential_pct=n[6], share_industrial_pct=n[7],
                        share_other_pct=n[8], share_nonthermal_pct=n[9],
                        share_thermal_pct=n[10])
        elif len(n) >= 9:           # 1346–1384: total losses only
            base.update(loss_total_pct=n[0], loss_transmission_pct=None,
                        loss_distribution_pct=None, thermal_efficiency_pct=n[1],
                        capacity_per_capita_w=n[2], generation_per_capita_kwh=n[3],
                        share_residential_pct=n[4], share_industrial_pct=n[5],
                        share_other_pct=n[6], share_nonthermal_pct=n[7],
                        share_thermal_pct=n[8])
        else:
            log(f"  [!] year {cur_year}: only {len(n)} numbers — skipped")
            cur_year, cur_nums = None, []
            return
        rows.append(base)
        cur_year, cur_nums = None, []

    for line in lines:
        # Plan-period interludes ("متوسط رشد سالانه ...") carry numbers that
        # would otherwise leak into the adjacent year's row and shift its
        # columns (this exact bug once put a per-capita wattage of 402 into
        # the distribution-loss column of 1378).
        if any(w in line for w in ("متوسط", "شروع", "درصد", "رشد")):
            continue
        toks = list(tokens(line))
        # Row label: the whole line is exactly the next expected year.
        if (len(toks) == 1 and toks[0][0] == "year" and toks[0][1] == expect):
            flush()
            cur_year, expect = toks[0][1], toks[0][1] + 1
            continue
        if cur_year is not None:
            cur_nums += [float(v) if k == "year" else v
                         for k, v in toks if k in ("year", "num")]
    flush()

    df = pd.DataFrame(rows)
    years = sorted(df.year)
    missing = sorted(set(range(1346, 1404)) - set(years))
    assert not missing, f"missing years: {missing}"
    # Cross-source anchor: the 1403 total loss must equal the officially
    # registered value parsed independently by stage 02 (10.32 per cent).
    assert abs(df.loc[df.year == 1403, "loss_total_pct"].iloc[0] - 10.32) < 1e-9
    assert df.loss_total_pct.between(5, 25).all(), "total loss out of range"
    assert df.loss_transmission_pct.dropna().between(1, 10).all(), "transmission loss out of range"
    assert df.loss_distribution_pct.dropna().between(5, 25).all(), "distribution loss out of range"

    out = write_tidy(df, "tavanir_losses_and_efficiency.csv", sort_by="year")
    log(f"wrote {out}: {len(df)} years; split available from "
        f"{int(df.dropna(subset=['loss_transmission_pct']).year.min())}")


if __name__ == "__main__":
    main()
