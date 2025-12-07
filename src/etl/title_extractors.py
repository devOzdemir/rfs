from __future__ import annotations
import re
import pandas as pd


# -----------------------------
# Helpers (public)
# -----------------------------
def missing_mask(s: pd.Series) -> pd.Series:
    """Boş/NaN/Yok/Belirtilmemiş gibi değerleri eksik kabul eder."""
    low = s.fillna("").astype(str).str.strip().str.lower()
    return s.isna() | low.isin(
        ["", "nan", "none", "null", "yok", "belirtilmemiş", "belirtilmemis", "-"]
    )


# -----------------------------
# Internal helpers
# -----------------------------
def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()


def _soft_clean(s: str) -> str:
    """
    SSD için kritik: 'i5 512GB SSD' -> 'i5 512gb ssd' (rakamlar birleşmez!)
    '-' '_' '/' gibi ayraçları boşluğa çevirir.
    """
    s = str(s).lower()
    s = re.sub(r"[-_/|]+", " ", s)
    s = s.replace(",", ".")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _fmt_storage_from_gb(gb: int) -> str:
    return f"{gb // 1024} TB" if gb >= 1024 and gb % 1024 == 0 else f"{gb} GB"


def _fmt_ram(v: int) -> str:
    return f"{v} GB"


# -----------------------------
# Regexler
# -----------------------------
GB_TOKEN = re.compile(r"(\d{1,4})\s*gb", re.IGNORECASE)
HZ_TOKEN = re.compile(r"(\d{1,3})\s*hz", re.IGNORECASE)

SSD_GB_RE = re.compile(
    r"(?<!\d)(\d{1,4})\s*gb\s*(?:nvme\s*)?(?:m\.?2\s*)?(?:ssd|gbssd)\b", re.IGNORECASE
)
SSD_TB_RE = re.compile(
    r"(?<!\d)(\d+(?:\.\d+)?)\s*tb\s*(?:nvme\s*)?(?:m\.?2\s*)?(?:ssd|gbssd)\b",
    re.IGNORECASE,
)

# Hepsiburada dağılımına göre izinli SSD kapasiteleri
ALLOWED_SSD_GB = {4, 120, 128, 250, 256, 500, 512, 1024, 2048, 4096, 8192}


def _validate_ssd_gb(gb: int | None) -> int | None:
    if gb is None:
        return None
    if gb <= 0 or gb > 8192:
        return None
    if gb not in ALLOWED_SSD_GB:
        return None
    return gb


FEATURES_PRIORITY = [
    "Retina",
    "OLED",
    "WQXGA",
    "WUXGA",
    "QHD+",
    "QHD",
    "Full HD",
    "FHD",
    "HD",
]
RES_RE = re.compile(r"(\d{3,4})\s*[x×X]\s*(\d{3,4})")

RES_MAP = {
    (1920, 1080): "Full HD",
    (1920, 1200): "WUXGA",
    (2560, 1600): "WQXGA",
    (2560, 1440): "QHD",
    (2880, 1800): "QHD+",
    (3200, 2000): "QHD+",
}
APPLE_RETINA_RES = {
    (2560, 1664),
    (2880, 1864),
    (3024, 1964),
    (3456, 2234),
    (3840, 2400),
}


# -----------------------------
# Row-level extractors (string -> value)
# -----------------------------
def ssd_gb_from_title(title: str) -> int | None:
    """SSD kapasitesini GB olarak döndürür (yoksa None)."""
    t = _soft_clean(title)
    cands: list[int] = []

    for m in SSD_TB_RE.finditer(t):
        gb = int(round(float(m.group(1)) * 1024))
        cands.append(gb)

    for m in SSD_GB_RE.finditer(t):
        cands.append(int(m.group(1)))

    if not cands:
        return None

    return _validate_ssd_gb(max(cands))


def ram_from_title(title: str) -> str | pd._libs.missing.NAType:
    """
    RAM:
    - SSD varsa: SSD'den önce gelen ilk 0–128 GB token'ı RAM
    - SSD yoksa: ilk 0–128 GB token'ı RAM
    - SSD kapasitesiyle aynı sayıyı RAM sayma
    """
    low = _norm(title).lower()
    tokens = [(int(m.group(1)), m.start(), m.end()) for m in GB_TOKEN.finditer(low)]
    if not tokens:
        return pd.NA

    ssd_pos = low.find("ssd")
    ssd_gb = ssd_gb_from_title(title)

    if ssd_pos != -1:
        for val, _, en in tokens:
            if 0 <= val <= 128 and en < ssd_pos:
                if ssd_gb is not None and val == ssd_gb:
                    continue
                return _fmt_ram(val)
        return pd.NA

    for val, _, _ in tokens:
        if 0 <= val <= 128:
            if ssd_gb is not None and val == ssd_gb:
                continue
            return _fmt_ram(val)

    return pd.NA


def ssd_from_title(title: str) -> str | pd._libs.missing.NAType:
    gb = ssd_gb_from_title(title)
    return _fmt_storage_from_gb(gb) if gb is not None else pd.NA


def refresh_rate_from_title(title: str) -> str | pd._libs.missing.NAType:
    vals = [int(m.group(1)) for m in HZ_TOKEN.finditer(str(title))]
    vals = [v for v in vals if 0 <= v <= 300]
    return f"{max(vals)} Hz" if vals else pd.NA


def screen_feature_from_title(title: str) -> str | pd._libs.missing.NAType:
    low = str(title).lower()

    if "liquid retina" in low:
        return "Retina"
    if "wqhd" in low:
        return "QHD"

    for feat in FEATURES_PRIORITY:
        if feat.lower() in low:
            return feat

    m = RES_RE.search(str(title))
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        if (w, h) in RES_MAP:
            return RES_MAP[(w, h)]
        if ("apple" in low or "macbook" in low) and (w, h) in APPLE_RETINA_RES:
            return "Retina"

    return pd.NA


# -----------------------------
# Column-level extractors (Series -> Series)
# -----------------------------
def extract_ram_from_title(title_series: pd.Series) -> pd.Series:
    return title_series.fillna("").astype(str).apply(ram_from_title).astype("object")


def extract_ssd_from_title(title_series: pd.Series) -> pd.Series:
    return title_series.fillna("").astype(str).apply(ssd_from_title).astype("object")


def extract_refresh_rate_from_title(title_series: pd.Series) -> pd.Series:
    return (
        title_series.fillna("")
        .astype(str)
        .apply(refresh_rate_from_title)
        .astype("object")
    )


def extract_screen_feature_from_title(title_series: pd.Series) -> pd.Series:
    return (
        title_series.fillna("")
        .astype(str)
        .apply(screen_feature_from_title)
        .astype("object")
    )


# -----------------------------
# Optional: fill helper (only missing)
# -----------------------------
def fill_column_from_title(
    df: pd.DataFrame,
    title_col: str,
    target_col: str,
    extractor,  # one of extract_*_from_title
) -> pd.DataFrame:
    """
    Sadece target_col eksikse doldurur.
    Kullanım: df = fill_column_from_title(df, "Başlık", "SSD Kapasitesi", extract_ssd_from_title)
    """
    out = df.copy()
    if target_col not in out.columns:
        out[target_col] = pd.NA

    parsed = extractor(out[title_col])
    m = missing_mask(out[target_col]) & parsed.notna()
    out.loc[m, target_col] = parsed.loc[m]
    return out
