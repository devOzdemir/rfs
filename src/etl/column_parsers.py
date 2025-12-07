from __future__ import annotations
import re
import numpy as np
import pandas as pd


# -----------------------------
# İşlemci Nesli -> float
# -----------------------------
def parse_cpu_generation(value, min_gen=1, max_gen=15):
    if pd.isna(value):
        return np.nan

    if isinstance(value, (int, float)):
        return float(value) if min_gen <= value <= max_gen else np.nan

    value = str(value).strip().lower()
    if value in [
        "belirtilmemiş",
        "belirtilmemis",
        "yok",
        "none",
        "-",
        "",
        "nan",
        "null",
    ]:
        return np.nan

    m = re.search(r"(\d+)\s*\.?\s*nesil", value)
    if m:
        g = int(m.group(1))
        return float(g) if min_gen <= g <= max_gen else np.nan

    m = re.search(r"series\s*(\d+)", value)
    if m:
        g = int(m.group(1))
        return float(g) if min_gen <= g <= max_gen else np.nan

    m = re.search(r"\bm\s*(\d+)\b", value)  # Apple M1..M5
    if m:
        g = int(m.group(1))
        return float(g) if min_gen <= g <= max_gen else np.nan

    if re.fullmatch(r"\d+", value):
        g = int(value)
        return float(g) if min_gen <= g <= max_gen else np.nan

    return np.nan


# -----------------------------
# Çekirdek Sayısı -> float
# -----------------------------
def parse_core_count(val, min_core=1, max_core=24):
    if pd.isna(val):
        return np.nan

    if isinstance(val, (int, float)):
        return float(val) if min_core <= val <= max_core else np.nan

    val = str(val).strip().lower()
    if val in ["belirtilmemiş", "belirtilmemis", "yok", "none", "-", "", "nan", "null"]:
        return np.nan

    m = re.match(r"(\d+)\+?", val)
    if m:
        core = int(m.group(1))
        return float(core) if min_core <= core <= max_core else np.nan

    return np.nan


# -----------------------------
# Maksimum İşlemci Hızı (GHz) -> float
# -----------------------------
def parse_max_cpu_freq(val, min_freq=1.0, max_freq=6.0):
    if pd.isna(val):
        return np.nan

    if isinstance(val, (int, float)):
        v = float(val)
        return v if min_freq <= v <= max_freq else np.nan

    val = str(val).strip().lower()
    val = val.replace("ghz", "").replace(" ", "").replace(",", ".")

    try:
        freq = float(val)
        return freq if min_freq <= freq <= max_freq else np.nan
    except ValueError:
        return np.nan


# -----------------------------
# RAM (GB) -> float
# -----------------------------
def parse_ram_size(val, min_ram=1, max_ram=256):
    if pd.isna(val):
        return np.nan

    if isinstance(val, (int, float)):
        ram = float(val)
    else:
        val = str(val).strip().lower()
        if val in [
            "belirtilmemiş",
            "belirtilmemis",
            "yok",
            "none",
            "",
            "-",
            "nan",
            "null",
        ]:
            return np.nan
        m = re.search(r"(\d+)", val)
        if not m:
            return np.nan
        ram = float(m.group(1))

    return ram if min_ram <= ram <= max_ram else np.nan


# -----------------------------
# GPU Memory (GB) -> float (Paylaşımlı -> shared_value)
# -----------------------------
def parse_gpu_memory(val, min_value=1, max_value=32, shared_value=0):
    if pd.isna(val):
        return np.nan

    if isinstance(val, (int, float)):
        v = float(val)
        return v if min_value <= v <= max_value else np.nan

    val = str(val).strip().lower()

    if "paylaşımlı" in val or "paylasimli" in val:
        return float(shared_value)

    if any(
        k in val
        for k in ["belirtilmemiş", "belirtilmemis", "none", "yok", "nan", "null"]
    ):
        return np.nan

    m = re.search(r"(\d+)\s*gb.*alt", val)
    if m:
        v = float(m.group(1))
        return v if min_value <= v <= max_value else np.nan

    m = re.search(r"(\d+)", val)
    if m:
        v = float(m.group(1))
        return v if min_value <= v <= max_value else np.nan

    return np.nan


# -----------------------------
# SSD / HDD Capacity (GB) -> float
# -----------------------------
def parse_capacity_gb(val, min_value=32, max_value=8000):
    """
    '512 GB', '1 TB', '256 GB; 512 GB', 'Yok' -> GB float
    """
    if pd.isna(val):
        return np.nan

    if isinstance(val, (int, float)):
        v = float(val)
        return v if min_value <= v <= max_value else np.nan

    val = str(val).strip().lower().replace(",", ".")
    if (
        "yok" in val
        or "belirtilmemiş" in val
        or "belirtilmemis" in val
        or val in ["none", "nan", "", "null"]
    ):
        return np.nan

    parts = re.split(r"[;|/]", val)
    best = 0.0

    for part in parts:
        part = part.strip()

        m_tb = re.search(r"(\d+(?:\.\d+)?)\s*tb", part)
        if m_tb:
            gb = float(m_tb.group(1)) * 1024
            best = max(best, gb)

        m_gb = re.search(r"(\d+(?:\.\d+)?)\s*gb", part)
        if m_gb:
            gb = float(m_gb.group(1))
            best = max(best, gb)

    return best if min_value <= best <= max_value else np.nan


# -----------------------------
# Screen size (inch) -> float
# -----------------------------
def parse_screen_size(val, min_value=7.0, max_value=20.0):
    if pd.isna(val):
        return np.nan

    if isinstance(val, (int, float)):
        v = float(val)
        return v if min_value <= v <= max_value else np.nan

    val = str(val).strip().lower()
    if val in ["belirtilmemiş", "belirtilmemis", "yok", "none", "nan", "", "null"]:
        return np.nan

    val = val.replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)\s*inç", val)
    if m:
        inch = float(m.group(1))
        return inch if min_value <= inch <= max_value else np.nan

    return np.nan


# -----------------------------
# Refresh rate (Hz) -> float
# -----------------------------
def parse_refresh_rate(val, min_value=30, max_value=360):
    if pd.isna(val):
        return np.nan

    if isinstance(val, (int, float)):
        v = float(val)
        return v if min_value <= v <= max_value else np.nan

    val = str(val).strip().lower()
    if val in ["belirtilmemiş", "belirtilmemis", "yok", "none", "nan", "", "null"]:
        return np.nan

    val = val.replace("hz", "").strip()
    try:
        hz = float(val)
        return hz if min_value <= hz <= max_value else np.nan
    except ValueError:
        return np.nan


# -----------------------------
# Price (TRY) -> float
# -----------------------------


def parse_price_try(val, min_value=1000, max_value=200000):
    if pd.isna(val):
        return np.nan

    if isinstance(val, (int, float)):
        v = float(val)
        return v if min_value <= v <= max_value else np.nan

    s = str(val).strip().lower()

    # tl/₺/boşluk gibi şeyleri temizle
    s = s.replace("₺", "").replace("tl", "")
    s = re.sub(r"\s+", "", s)

    # sadece rakam ve ayırıcılar kalsın
    s = re.sub(r"[^0-9,\.]", "", s)

    # TR formatı: 44.799,23 -> 44799.23
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        # 45.999 -> 45999 (binlik ayırıcı varsay)
        if "." in s:
            parts = s.split(".")
            if len(parts[-1]) == 3:  # binlik ayırıcı heuristiği
                s = "".join(parts)
        # 44799,23 -> 44799.23
        if "," in s:
            s = s.replace(",", ".")

    try:
        price = float(s)
    except ValueError:
        return np.nan

    return price if min_value <= price <= max_value else np.nan


# -----------------------------
# Uygulama yardımcıları
# -----------------------------
def apply_parser(df: pd.DataFrame, col: str, fn) -> pd.DataFrame:
    """df[col] = df[col].apply(fn) kısayolu."""
    df[col] = df[col].apply(fn)
    return df


def apply_all_parsers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sende kullandığın kolonlar için tek seferde uygular.
    Kolon yoksa atlar.
    """
    mapping = {
        "İşlemci Nesli": parse_cpu_generation,
        "İşlemci Çekirdek Sayısı": parse_core_count,
        "Maksimum İşlemci Hızı": parse_max_cpu_freq,
        "Ram (Sistem Belleği)": parse_ram_size,
        "Ekran Kartı Hafızası": parse_gpu_memory,
        "SSD Kapasitesi": parse_capacity_gb,
        "Harddisk Kapasitesi": parse_capacity_gb,
        "Ekran Boyutu": parse_screen_size,
        "Ekran Yenileme Hızı": parse_refresh_rate,
        "Fiyat (TRY)": parse_price_try,
    }

    for col, fn in mapping.items():
        if col in df.columns:
            df[col] = df[col].apply(fn)

    return df


# -----------------------------
# ortak yardımcı
# -----------------------------
def _na_if_invalid(s: str):
    invalids = {"", "nan", "none", "null", "-", "yok", "belirtilmemiş", "belirtilmemis"}
    return pd.NA if s in invalids else s


def _norm_text(val) -> str | pd._libs.missing.NAType:
    if pd.isna(val):
        return pd.NA
    s = str(val).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return _na_if_invalid(s)


# -----------------------------
# BRAND standardizasyonu
# -----------------------------
BRAND_MAP = {
    "hp": "hp",
    "hewlett packard": "hp",
    "h.p.": "hp",
    "lenovo": "lenovo",
    "asus": "asus",
    "dell": "dell",
    "msi": "msi",
    "acer": "acer",
    "monster": "monster",
    "casper": "casper",
    "game garaj": "game garaj",
    "erazer": "erazer",
    "huawei": "huawei",
    "samsung": "samsung",
    "gigabyte": "gigabyte",
    "hometech": "hometech",
    "xiaomi": "xiaomi",
    "microsoft": "microsoft",
    "toshiba": "toshiba",
    "tecno": "tecno",
    # i-life varyasyonları
    "i-life": "i-life",
    "ilife": "i-life",
    "i-life digital": "i-life",
}


def parse_brand(val):
    """
    Marka standardizasyonu (lower/strip + mapping).
    """
    s = _norm_text(val)
    if s is pd.NA:
        return pd.NA
    return BRAND_MAP.get(s, s)


# -----------------------------
# Intended use standardizasyonu
# -----------------------------
def parse_intended_use(val):
    """
    intended_use kategorilerini az sayıda ana sınıfa toplar.
    """
    s = _norm_text(val)
    if s is pd.NA:
        return pd.NA

    # Türkçe karakter sapmaları / birleşik yazımlar için kaba eşleme
    if "oyun" in s:
        return "oyun"
    if "ofis" in s or "iş" in s or "is" in s:
        return "ofis-is"
    if "ev" in s and ("okul" in s or "öğrenci" in s or "ogrenci" in s):
        return "ev-okul"
    if "tasarım" in s or "tasarim" in s:
        return "tasarım"

    # ev tek başına geldiyse
    if s == "ev":
        return "ev"

    return s


# -----------------------------
# Color standardizasyonu
# -----------------------------
def parse_color(val):
    """
    Renk kolonunu tek renge indirir:
    - ayraçlarla ayrılmışsa ilk rengi alır
    - unicode sapmalarını temizler (si̇yah -> siyah, gri̇ -> gri, laci̇vert -> lacivert)
    - gri ailesini tek "gri" altında toplar (koyu gri, metalik gri, titanyum gri -> gri)
    """
    if pd.isna(val):
        return pd.NA

    s = str(val).strip().lower()
    s = re.sub(r"\s+", " ", s)

    invalids = {"", "nan", "none", "null", "-", "yok", "belirtilmemiş", "belirtilmemis"}
    if s in invalids:
        return pd.NA

    # ayraçları birleştir
    s = s.replace(";", ",").replace("/", ",").replace("|", ",").replace("-", ",")
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if not parts:
        return pd.NA

    first = parts[0]

    # unicode dotted-i gibi sapmaları kaba düzelt
    first = first.replace("si̇", "si").replace("gri̇", "gri").replace("laci̇", "laci")

    # İngilizce -> TR
    basic_map = {
        "black": "siyah",
        "white": "beyaz",
        "grey": "gri",
        "gray": "gri",
        "silver": "gümüş",
        "blue": "mavi",
    }
    first = basic_map.get(first, first)

    # gri ailesini tekle
    if "gri" in first or "grey" in first or "gray" in first:
        return "gri"

    # siyah ailesi
    if "siyah" in first or "black" in first or "onyx" in first:
        return "siyah"

    # mavi ailesi
    if "mavi" in first or "lacivert" in first or "blue" in first:
        return "mavi"

    # gümüş ailesi
    if "gümüş" in first or "silver" in first:
        return "gümüş"

    # beyaz
    if "beyaz" in first or "white" in first:
        return "beyaz"

    # renksiz/genel
    if first in {"renkli", "çok renkli", "cok renkli"}:
        return "renkli"

    return first


# -----------------------------
# Weight standardizasyonu
# -----------------------------
def parse_weight(val):
    """
    weight: kesin kg değerlerini aralıklara yerleştirir:
      <=2.0  -> "2 kg ve altı"
      (2.0,4.0] -> "2 - 4 kg"
      >4.0   -> "4 kg ve üzeri"
    Zaten aralık ise standardize eder.
    """
    if pd.isna(val):
        return pd.NA

    s = str(val).strip().lower()
    s = re.sub(r"\s+", " ", s)

    invalids = {"", "nan", "none", "null", "-", "yok", "belirtilmemiş", "belirtilmemis"}
    if s in invalids:
        return pd.NA

    # Zaten aralık/kategori ise
    s_norm = s.replace("ı", "i").replace("ve üzeri", "ve uzeri")

    if "2 kg ve alti" in s_norm or "2 kg ve alt" in s_norm:
        return "2 kg ve altı"
    if "1 - 2 kg" in s_norm or "1-2 kg" in s_norm:
        return "1 - 2 kg"
    if "2 - 4 kg" in s_norm or "2-4 kg" in s_norm:
        return "2 - 4 kg"
    if "4 kg ve uzeri" in s_norm:
        return "4 kg ve üzeri"

    # Kesin kg yakala: "1,65 kg", "2.2 kg", "2 kg"
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*kg", s_norm)
    if m:
        w = m.group(1).replace(",", ".")
        try:
            w = float(w)
        except ValueError:
            return pd.NA

        if w <= 0 or w > 10:
            return pd.NA

        if w <= 2.0:
            return "2 kg ve altı"
        elif w <= 4.0:
            return "2 - 4 kg"
        else:
            return "4 kg ve üzeri"

    return pd.NA


# -------------------------
# CPU Family standardizasyonu
# -------------------------
def parse_cpu_family(val):
    if pd.isna(val):
        return pd.NA

    if isinstance(val, (int, float)):
        return pd.NA

    s = str(val).strip().lower()
    s = re.sub(r"\s+", " ", s)

    invalids = {"", "nan", "none", "null", "-", "yok", "belirtilmemiş", "belirtilmemis"}
    if s in invalids:
        return pd.NA

    # bariz çöp değerler
    if s in {"ip", "xp"}:
        return "unknown"

    # normalize varyasyonlar
    s = s.replace("ultra core", "core ultra")
    s = s.replace("intel alder lake n100", "intel n100")
    s = s.replace("qualcomm snapdragon x elite", "qualcomm snapdragon x")
    s = s.replace("snapdragon x elite", "qualcomm snapdragon x")
    s = s.replace("snapdragon x plus", "qualcomm snapdragon x")
    if s == "snapdragon x":
        s = "qualcomm snapdragon x"
    if s == "core ultra 7":
        s = "intel core ultra 7"

    # -------------------------
    # Intel Core Ultra 5/7/9
    # -------------------------
    m = re.search(r"(?:intel\s*)?core ultra\s*(5|7|9)\b", s)
    if m:
        return f"intel core ultra {m.group(1)}"

    # "intel ultra 7", "intel ultra core 7", "intel ultra 5" -> core ultra
    m = re.search(r"\bintel\s*ultra(?:\s*core)?\s*(5|7|9)\b", s)
    if m:
        return f"intel core ultra {m.group(1)}"

    # -------------------------
    # Intel Core i3/i5/i7/i9
    # -------------------------
    m = re.search(r"\bcore\s*i\s*([3579])\b", s)
    if m:
        return f"intel core i{m.group(1)}"

    # "intel core 5/7/9" veya "intel core 7/9" -> i'siz isimleri i'li standarda çek
    m = re.search(r"\bintel\s*core\s*(5|7|9)\b", s)
    if m:
        return f"intel core i{m.group(1)}"

    # -------------------------
    # Intel Celeron / Core M / N-series
    # -------------------------
    if "celeron" in s:
        return "intel celeron"

    if re.search(r"\bintel\s*n\d+\b", s) or re.fullmatch(r"n\d{2,4}", s):
        return "intel n-series"

    if re.search(r"\bcore m\b", s) or "intel core m" in s:
        return "intel core m"

    # -------------------------
    # AMD Ryzen AI 7/9 (hx/max+/z2 vb dahil)
    # -------------------------
    if "ryzen ai" in s:
        m = re.search(r"ryzen ai\s*(7|9)\b", s)
        if m:
            return f"amd ryzen ai {m.group(1)}"
        return "amd ryzen ai"

    # -------------------------
    # AMD Ryzen 3/5/7/9 (+ z2 dahil)
    # -------------------------
    m = re.search(r"\bryzen\s*(3|5|7|9)\b", s)
    if m:
        return f"amd ryzen {m.group(1)}"

    # "amd ryzen z2" / "amd ryzen ai z2" gibi -> aile belirsiz, ai değilse ryzen olarak işaretle
    if "ryzen z2" in s:
        return "amd ryzen"

    # -------------------------
    # Qualcomm Snapdragon X
    # -------------------------
    if "qualcomm snapdragon x" in s or "snapdragon x" in s:
        return "qualcomm snapdragon x"

    # -------------------------
    # AMD legacy
    # -------------------------
    if (
        "athlon" in s
        or re.search(r"\bamd\s*a\d+\b", s)
        or s == "amd e"
        or "e-series" in s
    ):
        return "amd legacy"

    # -------------------------
    # Other
    # -------------------------
    if "mediatek" in s:
        return "mediatek"

    if "intel tabanlı" in s or "intel tabanli" in s:
        return "intel"

    return "unknown"


# -----------------------------
# RAM Type standardizasyonu
# ----------------------------
def parse_ram_type(val):
    """
    ram_type standardizasyonu:
    - ddr3/ddr4/ddr5
    - lpddr3/lpddr4x/lpddr5/lpddr5x
    - birleşik bellek -> unified
    - hatalı/uydurma (ddr15, ddr6, ddr1 vs) -> NA
    """
    if pd.isna(val):
        return pd.NA

    if isinstance(val, (int, float)):
        return pd.NA

    s = str(val).strip().lower()
    s = re.sub(r"\s+", " ", s)

    invalids = {"", "nan", "none", "null", "-", "yok", "belirtilmemiş", "belirtilmemis"}
    if s in invalids:
        return pd.NA

    # birleşik bellek
    if "birleşik bellek" in s or "birlesik bellek" in s or "unified" in s:
        return "unified"

    # normalize yazımlar
    s = s.replace("-", "").replace("_", "")

    # LPDDR önce kontrol (ddr ile karışmasın)
    if "lpddr" in s:
        # lpddr5x
        if re.search(r"lpddr\s*5x", s) or "lpddr5x" in s:
            return "lpddr5x"
        # lpddr5
        if re.search(r"lpddr\s*5\b", s) or "lpddr5" in s:
            return "lpddr5"
        # lpddr4x
        if re.search(r"lpddr\s*4x", s) or "lpddr4x" in s:
            return "lpddr4x"
        # lpddr4
        if re.search(r"lpddr\s*4\b", s) or "lpddr4" in s:
            return "lpddr4"
        # lpddr3
        if re.search(r"lpddr\s*3\b", s) or "lpddr3" in s:
            return "lpddr3"
        return pd.NA

    # DDR
    if "ddr" in s:
        # sadece 3/4/5 geçerli kabul edelim
        m = re.search(r"ddr\s*([0-9]+)", s)
        if m:
            gen = m.group(1)
            if gen in {"3", "4", "5"}:
                return f"ddr{gen}"
            return pd.NA
        return pd.NA

    return pd.NA


# -----------------------------
# GPU standardizasyonu
# ----------------------------


def parse_gpu_model(val):
    """
    gpu_model standardizasyonu:
    - NVIDIA: rtx/gtx/mx + model numarası -> 'nvidia rtx 4060' gibi
    - Intel/AMD entegre -> 'intel integrated' / 'amd integrated'
    - Qualcomm -> 'qualcomm adreno'
    - onboard/paylaşımlı/dahili -> 'integrated'
    - Ada workstation -> 'nvidia rtx ada'
    - diğerleri -> 'unknown'
    """
    if pd.isna(val):
        return pd.NA

    if isinstance(val, (int, float)):
        return pd.NA

    s = str(val).strip().lower()
    s = re.sub(r"\s+", " ", s)

    invalids = {"", "nan", "none", "null", "-", "yok", "belirtilmemiş", "belirtilmemis"}
    if s in invalids:
        return pd.NA

    # genel "entegre/paylaşımlı"
    if any(
        k in s
        for k in [
            "paylaşımlı",
            "paylasimli",
            "onboard",
            "dahili ekran kartı",
            "dahili ekran karti",
            "integrated",
        ]
    ):
        return "integrated"

    # Qualcomm Adreno
    if "adreno" in s:
        return "qualcomm adreno"

    # --- NVIDIA standardizasyonu ---
    # Ada workstation: "nvidia rtx 2000 ada", "500 ada nesli", "5000 ada nesli"
    if "ada" in s and "rtx" in s:
        return "nvidia rtx ada"

    # rtx: "nvidia geforce rtx 5070 ti", "rtx3070ti", "rtx 3050 ti"
    m = re.search(r"\brtx\s*([0-9]{3,4})\s*(ti)?\b", s.replace("geforce", ""))
    if m:
        num = m.group(1)
        ti = " ti" if m.group(2) else ""
        return f"nvidia rtx {num}{ti}".strip()

    # gtx: "gtx 1650", "gtx1650 ti"
    m = re.search(r"\bgtx\s*([0-9]{3,4})\s*(ti)?\b", s.replace("geforce", ""))
    if m:
        num = m.group(1)
        ti = " ti" if m.group(2) else ""
        return f"nvidia gtx {num}{ti}".strip()

    # mx: "mx330", "geforce mx450"
    m = re.search(r"\bmx\s*([0-9]{3})\b", s)
    if m:
        return f"nvidia mx {m.group(1)}"

    # "nvidia geforce" geçip model yakalanamadıysa
    if "nvidia" in s:
        return "nvidia (other)"

    # --- Intel ---
    if "intel" in s:
        # marka içi ayrıntıyı sadeleştir (uhd/iris/arc/xe/hd)
        return "intel integrated"

    # --- AMD ---
    if "amd" in s or "radeon" in s:
        return "amd integrated"

    return "unknown"


# -----------------------------
# GPU tip standardizasyonu
# ----------------------------
def parse_gpu_type(val):
    """
    gpu_type standardizasyonu:
      - 'dahili', 'dahili ekran kartı', 'onboard' -> integrated
      - 'harici', 'harici ekran kartı' -> dedicated
      - 'yüksek seviye harici ekran kartı' -> dedicated_high_end
      - 'paylaşımlı' -> shared
    """
    if pd.isna(val):
        return pd.NA

    if isinstance(val, (int, float)):
        return pd.NA

    s = str(val).strip().lower()
    s = re.sub(r"\s+", " ", s)

    invalids = {"", "nan", "none", "null", "-", "yok", "belirtilmemiş", "belirtilmemis"}
    if s in invalids:
        return pd.NA

    # normalize varyasyonlar
    s = s.replace("paylasimli", "paylaşımlı")

    if "yüksek seviye" in s and "harici" in s:
        return "dedicated_high_end"

    if "paylaşımlı" in s:
        return "shared"

    # onboard'u integrated altında birleştir
    if "onboard" in s or "dahili" in s:
        return "integrated"

    if "harici" in s:
        return "dedicated"

    return "unknown"


# -----------------------------
# GPU vram type standardizasyonu
# ----------------------------


def parse_gpu_vram_type(val):
    """
    gpu_vram_type standardizasyonu:
      - gddr4/5/5x/6/6x/7
      - ddr3/4/5
      - paylaşımlı/onboard/dahili -> shared
      - geçersiz -> NA
    """
    if pd.isna(val):
        return pd.NA

    if isinstance(val, (int, float)):
        return pd.NA

    s = str(val).strip().lower()
    s = re.sub(r"\s+", " ", s)

    invalids = {"", "nan", "none", "null", "-", "yok", "belirtilmemiş", "belirtilmemis"}
    if s in invalids:
        return pd.NA

    s = s.replace("paylasimli", "paylaşımlı")

    # shared ifadeleri
    if any(k in s for k in ["paylaşımlı", "paylasimli", "onboard", "dahili", "shared"]):
        return "shared"

    # normalize
    s = s.replace("-", "").replace("_", "").replace(" ", "")

    # gddr
    m = re.fullmatch(r"gddr(4|5|5x|6|6x|7)", s)
    if m:
        return "gddr" + m.group(1)

    # ddr (sadece 3/4/5 kabul)
    m = re.fullmatch(r"ddr(3|4|5)", s)
    if m:
        return "ddr" + m.group(1)

    # bazen "ddr5" gibi yazılmış olur (yukarı yakalar)
    # "ddr" tek başına, "ddr6", "sd" gibi şeyleri NA yap
    return pd.NA


# -----------------------------
# Resolution standardizasyonu
# ----------------------------


def parse_resolution(val, min_w=800, min_h=500, max_w=10000, max_h=10000):
    """
    resolution standardizasyonu: '1920 x 1080' -> '1920x1080'
    - x / X / × destekler
    - min/max aralığı dışında NA
    """
    if pd.isna(val):
        return pd.NA

    if isinstance(val, (int, float)):
        return pd.NA

    s = str(val).strip().lower()
    s = re.sub(r"\s+", " ", s)

    invalids = {"", "nan", "none", "null", "-", "yok", "belirtilmemiş", "belirtilmemis"}
    if s in invalids:
        return pd.NA

    # "×" ve "X" -> "x"
    s = s.replace("×", "x").replace("X", "x")

    m = re.search(r"(\d{3,5})\s*x\s*(\d{3,5})", s)
    if not m:
        return pd.NA

    w = int(m.group(1))
    h = int(m.group(2))

    if not (min_w <= w <= max_w and min_h <= h <= max_h):
        return pd.NA

    return f"{w}x{h}"


# -----------------------------
# Display Standard standardizasyonu
# ----------------------------


def parse_display_standard(val):
    """
    display_standard standardizasyonu:
      - 'full hd', 'fhd', 'full hd (fhd)', 'full hd ultra wide' -> fhd
      - 'hd', 'hd ready (hd)' -> hd
      - 'wuxga' -> wuxga
      - 'qhd' -> qhd
      - 'qhd+' -> qhd_plus
      - 'wqxga' -> wqxga
      - 'wqhd' -> wqhd
      - 'ultra hd 4k (uhd)' -> uhd_4k
      - 'oled', 'oled 2.8k', 'oled 3.2k' -> oled
      - '2.5k' gibi -> other
      - 'dokunmatik' -> other
    """
    if pd.isna(val):
        return pd.NA

    if isinstance(val, (int, float)):
        return pd.NA

    s = str(val).strip().lower()
    s = re.sub(r"\s+", " ", s)

    invalids = {"", "nan", "none", "null", "-", "yok", "belirtilmemiş", "belirtilmemis"}
    if s in invalids:
        return pd.NA

    # OLED her şeyi ezer (oled 3.2k gibi)
    if "oled" in s:
        return "oled"

    # UHD / 4K
    if "uhd" in s or "4k" in s or "ultra hd" in s:
        return "uhd_4k"

    # WQXGA
    if "wqxga" in s:
        return "wqxga"

    # WUXGA
    if "wuxga" in s:
        return "wuxga"

    # WQHD
    if "wqhd" in s:
        return "wqhd"

    # QHD+
    if "qhd+" in s or "qhd +" in s:
        return "qhd_plus"

    # QHD
    if re.search(r"\bqhd\b", s):
        return "qhd"

    # FHD / Full HD
    if "full hd" in s or re.search(r"\bfhd\b", s):
        return "fhd"

    # HD
    if "hd ready" in s or re.search(r"\bhd\b", s):
        return "hd"

    # dokunmatik / 2.5k / ultra wide vb. "standart" dışı
    if (
        "dokunmatik" in s
        or "touch" in s
        or "2.5k" in s
        or "3.2k" in s
        or "ultra wide" in s
    ):
        return "other"

    return "other"


# -----------------------------
# Panel tipi standardizasyonu
# ----------------------------


def parse_panel_type(val):
    """
    panel_type standardizasyonu:
    Geçerli panel teknolojileri: ips, tn, va, wva, sva, oled, lcd, led, mini led, tft, ltps
    Panel teknolojisi olmayan ifadeler (fhd, wuxga, qhd, 4k uhd, anti-glare, mikro kenarlı vb.) -> NA
    """
    if pd.isna(val):
        return pd.NA

    if isinstance(val, (int, float)):
        return pd.NA

    s = str(val).strip().lower()
    s = re.sub(r"\s+", " ", s)

    invalids = {"", "nan", "none", "null", "-", "yok", "belirtilmemiş", "belirtilmemis"}
    if s in invalids:
        return pd.NA

    # panel olmayanlar -> NA
    non_panel_tokens = [
        "fhd",
        "full hd",
        "wuxga",
        "wqxga",
        "qhd",
        "qhd+",
        "4k",
        "uhd",
        "anti-glare",
        "antiglare",
        "mikro kenarlı",
        "mikro kenarli",
        "micro bezel",
        "dokunmatik",
        "touch",
    ]
    if any(t in s for t in non_panel_tokens):
        return pd.NA

    # normalize "va / fhd" gibi şeylerde va'yı al
    s = s.replace("/", " ")
    parts = [p for p in s.split() if p]

    # mini led
    if "mini" in parts and "led" in parts:
        return "mini led"

    # geçerli panel keyword'leri
    valid = {"ips", "tn", "va", "wva", "sva", "oled", "lcd", "led", "tft", "ltps"}
    for p in parts:
        if p in valid:
            return p

    return pd.NA


# -----------------------------
# Isletim Sistemi standardizasyonu
# ----------------------------


def parse_operating_system(val):
    """
    operating_system standardizasyonu:
      - freedos/yok -> freedos
      - android -> linux
      - ubuntu -> ubuntu
      - linux -> linux
      - windows 10/11/... -> windows pro | windows home
      - sadece 'windows' -> windows home
    """
    if pd.isna(val):
        return pd.NA

    if isinstance(val, (int, float)):
        return pd.NA

    s = str(val).strip().lower()
    s = re.sub(r"\s+", " ", s)

    invalids = {"", "nan", "none", "null", "-", "belirtilmemiş", "belirtilmemis"}
    if s in invalids:
        return pd.NA

    # freedos / işletim sistemi yok
    if (
        ("free dos" in s)
        or ("freedos" in s)
        or ("işletim sistemi yok" in s)
        or ("isletim sistemi yok" in s)
        or s.startswith("yok")
    ):
        return "freedos"

    # android -> linux altında
    if "android" in s:
        return "linux"

    # ubuntu
    if "ubuntu" in s:
        return "ubuntu"

    # linux
    if s == "linux" or ("linux" in s and "windows" not in s):
        return "linux"

    # windows ailesi: pro/home'a indir
    if "windows" in s:
        if "pro" in s:
            return "windows pro"
        if "home" in s or "single language" in s:
            return "windows home"
        # sadece "windows" veya sürüm var ama home/pro yok -> home kabul et
        return "windows home"

    return "unknown"
