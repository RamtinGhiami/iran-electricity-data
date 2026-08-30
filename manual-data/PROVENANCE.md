# Provenance — manually collected official data

Rule (same as the inflation project): **every file in this tree carries a
row here** — what it is, which site it came from, when, and which pipeline
stage reads it. A file whose source cannot be stated does not get used.
When you add a file, tell Claude the site/URL so this table stays complete.

## amar.org.ir — Statistical Centre of Iran (SCI)

Downloaded manually from amar.org.ir (no API; VPN off), 2026-08-29
(7 Shahrivar 1405).

| File(s) | What | Used by |
|---|---|---|
| `amar.org.ir/sci-household/household_urban_1390.pdf`, `_1395.pdf`, `_1404_summary.pdf` | نتایج آمارگیری از مصرف حامل‌های انرژی خانوارهای شهری — household energy-carrier consumption surveys (full reports 1390, 1395; abstract 1404) | household-demand stage (planned) |
| `amar.org.ir/sci-kargah-sanati/kargah_1383.xls … kargah_1402.xls` | نتایج آمارگیری از مقدار مصرف انرژی در کارگاه‌های صنعتی ۱۰+ نفر کارکن — industrial workshops energy survey, 20 annual workbooks | industrial-demand stage (planned) |

## amar.tavanir.org.ir — Tavanir statistics portal

Downloaded manually (VPN off), 2026-08-29.

| File(s) | What | Used by |
|---|---|---|
| `tavanir/long-series/58sal_sanat_bargh.pdf` | «۵۸ سال صنعت برق ایران در آیینهٔ آمار» (1346–1403) | `01_parse_peak_history.py`, `05_parse_losses_and_efficiency.py` |
| `tavanir/long-series/ravand_10saleh_ta1403.pdf` | «روند ده‌سالهٔ صنعت برق» (207 pp) | reserve / cross-checks |
| `tavanir/amar-rasmi/rasmi_1399.xlsx … rasmi_1404.xlsx` | «آمارهای رسمی صنعت برق» — officially registered single-year indicator workbooks | `02_parse_official_yearbooks.py` |
| `tavanir/peak/pik_mahane_1404_1405.pdf` | «پیک بار همزمان با شبکهٔ سراسری» — monthly peaks | `03_parse_monthly_peaks.py` |
| `tavanir/tafsili-enteghal/enteghal_1398…1403.pdf` | آمار تفصیلی، ویژهٔ انتقال | losses/grid stage (planned) |
| `tavanir/tafsili-tozee/tozee_1398…1403.pdf` | آمار تفصیلی، ویژهٔ توزیع | tariff-class sales / distribution losses (planned) |

## Tariffs and prices

| File(s) | What | Source | Used by |
|---|---|---|---|
| `tarefe/forush_energy_by_sector_1378plus.xlsx` | فروش انرژی برق به تفکیک نوع مصرف، از ۱۳۷۸ (میلیون کیلووات‌ساعت؛ جدول «۲۸» از یک سالنامه/گزارش) | **TO CONFIRM — عنوان سایت/سند را کاربر اعلام کند** | sectoral-demand stage (planned) |

A Ministry of Energy circular on connection-fee amendments (ابلاغیهٔ
اصلاحیهٔ هزینه‌های انشعاب، ۱۴۰۴/۱۰/۰۸, referencing dotic.ir/qavanin.ir) was
inspected and removed by the user; re-add with its URL if needed.

Still wanted: متوسط بهای فروش و قیمت تمام‌شدهٔ برق (Tavanir performance/
financial report) and SATBA guaranteed-purchase tariffs.

**Registration-gated (documented as a limitation, not obtained):**
«پروژه‌های صنعت برق» and «پیش‌بینی آماری صنعت برق» on amar.tavanir.org.ir,
and the national energy balance (ترازنامهٔ انرژی وزارت نیرو), all sit behind
user registration (2026-08-29). The paper's data section should note that
the official capacity pipeline, the official demand forecast and the energy
balance exist but are not retrievable without an account.

## International mirror (fetched programmatically by Claude, VPN on)

| File | What | Source | Used by |
|---|---|---|---|
| `../electricity/data/raw/owid_energy.csv` | OWID energy dataset (Ember / Energy Institute compilation); Iran + World generation 1985–2025 | https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv, fetched 2026-08-29 (Ember's own bucket refuses this network location) | `06_parse_world_generation.py` |
