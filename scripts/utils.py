# -*- coding: utf-8 -*-
"""Shared helpers for the electricity pipeline: paths, Persian text
normalisation, and deterministic CSV output. Parsers read only the local
files under manual-data/ — no network access."""
import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                            # repo root
MANUAL = os.path.join(ROOT, "manual-data")
E_DATA = os.path.join(ROOT, "data", "sources")
E_RESULTS = os.path.join(ROOT, "results")
os.makedirs(E_DATA, exist_ok=True)
os.makedirs(E_RESULTS, exist_ok=True)

# Solar Hijri month names as they appear (attached to digits) in Tavanir PDFs.
MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
          "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
# The PDFs use Arabic Yeh/Kaf glyph variants; normalise before matching.
_GLYPHS = str.maketrans({"ي": "ی", "ك": "ک", "ﯽ": "ی", "ﯼ": "ی",
                         "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
                         "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
                         "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
                         "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9"})


def norm(s: str) -> str:
    """Normalise glyph variants and digits; keep text otherwise untouched.

    NFKC first: Tavanir PDFs embed Arabic presentation forms (U+FBxx/FExx),
    which NFKC folds back to standard letters before the variant mapping.
    """
    import unicodedata
    return unicodedata.normalize("NFKC", s).translate(_GLYPHS)


def tokens(line: str):
    """Split a PDF line into an ordered stream of typed tokens.

    Tavanir's PDF text glues numbers, month names and dashes together
    ("1403تیر64441", "64635مرداد62508مرداد80065", "ـ39/8"). Downstream
    parsers reason over the token order, not the raw line.
    Yields ("year", int) | ("month", str) | ("num", float) | ("dash", None).
    """
    s = norm(line)
    month_re = "|".join(MONTHS)
    # Year alternative must be a standalone 4-digit group: without the
    # lookarounds, "13308" (a megawatt value) would tokenise as year 1330 + 8.
    # Numbers accept both the Persian slash decimal (39/65) and, in a few
    # footnoted cells of the indicator table, a dot decimal (19.9*).
    pat = re.compile(rf"((?<!\d)(?:13\d\d|14\d\d)(?![\d/.]))|({month_re})|(\d+(?:[/.]\d+)?)|(ـ)")
    for m in pat.finditer(s):
        if m.group(1):
            yield ("year", int(m.group(1)))
        elif m.group(2):
            yield ("month", m.group(2))
        elif m.group(3):
            yield ("num", float(m.group(3).replace("/", ".")))
        elif m.group(4):
            yield ("dash", None)


def write_tidy(df: pd.DataFrame, name: str, sort_by=None) -> str:
    """Deterministic CSV write: stable order, %g floats, LF, utf-8-sig."""
    out = os.path.join(E_DATA, name)
    if sort_by:
        df = df.sort_values(sort_by).reset_index(drop=True)
    df.to_csv(out, index=False, encoding="utf-8-sig", lineterminator="\n",
              float_format="%.6g")
    return out


def log(msg: str) -> None:
    print(msg, flush=True)
