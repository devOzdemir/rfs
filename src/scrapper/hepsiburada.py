import os
import time
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By

LINK_DIR = "../../data/link"
RAW_DIR = "../../data/raw"
PROCESSED_DIR = "../../data/processed"

# Use an absolute log folder so logs don't end up in an unexpected CWD
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d%H%M")
log_file = LOG_DIR / f"HB_Scraper_{timestamp}.log"


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

# Dedicated logger to avoid clashing with Trendyol (or other modules) in the same process.
logger = logging.getLogger("scrapper.hepsiburada")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter(LOG_FORMAT)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

# Prevent logs from bubbling up to the root logger (which may have TY_Scraper handlers)
logger.propagate = False


# Hepsiburada - Ürün detay sayfasında gözüken teknik özellik alanlarının hedef listesi
# (label'lar, sayfada görünen isimlerle birebir eşleşmelidir)
TARGET_FIELDS = [
    # Genel
    "Başlık",
    "Marka",
    "Ürün Modeli",
    "Kullanım Amacı",
    "Renk",
    "Cihaz Ağırlığı",
    # İşlemci
    "İşlemci Tipi",
    "İşlemci",
    "İşlemci Nesli",
    "İşlemci Çekirdek Sayısı",
    "İşlemci Cache",
    "Temel İşlemci Hızı",
    "Maksimum İşlemci Hızı",
    # Bellek
    "Ram (Sistem Belleği)",
    "Ram Tipi",
    "Bellek Hızı",
    # Depolama
    "SSD Kapasitesi",
    "Harddisk Kapasitesi",
    # Ekran
    "Ekran Boyutu",
    "Ekran Panel Tipi",
    "Max Ekran Çözünürlüğü",
    "Ekran Özelliği",
    "Ekran Yenileme Hızı",
    # Grafik
    "Ekran Kartı Tipi",
    "Ekran Kartı",
    "Ekran Kartı İşlemcisi",
    "Ekran Kartı Hafızası",
    "Ekran Kartı Bellek Tipi",
    # Yazılım
    "İşletim Sistemi",
]


def get_product_links(base_url: str, total_pages: int = 1, driver=None) -> pd.DataFrame:
    """
    Hepsiburada'dan ürün başlıklarını, fiyatlarını ve linklerini çeker.
    """
    all_results = []

    for page in range(1, total_pages + 1):
        logger.info(f"Processing page {page}...")
        driver.get(base_url + str(page))
        time.sleep(3)

        items = driver.find_elements(By.TAG_NAME, "li")

        for item in items:
            try:
                a_tag = item.find_element(By.TAG_NAME, "a")
                title = a_tag.get_attribute("title")
                link = a_tag.get_attribute("href")

                price_tag = item.find_element(
                    By.CSS_SELECTOR, "[data-test-id^='final-price']"
                )
                price = price_tag.text.replace("\n", " ").strip()

                all_results.append({"Name": title, "Price": price, "Link": link})
            except Exception:
                continue

    df = pd.DataFrame(all_results)
    return df


def get_product_details(link: str, driver) -> dict:
    """
    Tek bir ürünün detay özelliklerini çeker.
    """
    features = {field: None for field in TARGET_FIELDS}

    try:
        driver.get(link)
        time.sleep(3)

        try:
            title_element = driver.find_element(
                By.CSS_SELECTOR, '[data-test-id="title"]'
            )
            brand_element = driver.find_element(
                By.CSS_SELECTOR, '[data-test-id="brand"]'
            )

            features["Başlık"] = title_element.text.strip()
            features["Marka"] = brand_element.get_attribute("title").strip()

        except Exception as e:
            logger.warning(f"Başlık veya marka bilgisi alınamadı: {link} - {e}")

        try:
            tech_specs = driver.find_element(By.ID, "techSpecs")
            rows = tech_specs.find_elements(By.CLASS_NAME, "jkj4C4LML4qv2Iq8GkL3")

            for row in rows:
                try:
                    label = row.find_element(
                        By.CLASS_NAME, "OXP5AzPvafgN_i3y6wGp"
                    ).text.strip()
                    value_element = row.find_element(
                        By.CLASS_NAME, "AxM3TmSghcDRH1F871Vh"
                    )

                    if value_element.find_elements(By.TAG_NAME, "a"):
                        value = (
                            value_element.find_element(By.TAG_NAME, "a")
                            .get_attribute("title")
                            .strip()
                        )
                    else:
                        value = value_element.text.strip()

                    if label in features and value:
                        # Aynı etiket tekrar gelirse (ör. Renk) değerleri kaybetmeden birleştir
                        if features[label] and features[label] != value:
                            features[label] = f"{features[label]}; {value}"
                        else:
                            features[label] = value

                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Teknik özellikler tablosu bulunamadı: {link} - {e}")

    except Exception as e:
        logger.error(f"Ürün detayları alınamadı: {e}")

    features["Çekilme Zamanı"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return features


def scrape_all_details(links_df: pd.DataFrame, driver) -> pd.DataFrame:
    """
    Ürün linkleri DataFrame'inden tüm ürün detaylarını döndüren DataFrame'i oluşturur.
    """
    results = []

    for i, (link, price) in enumerate(
        zip(links_df["Link"], links_df["Price"]), start=1
    ):
        if i % 50 == 0 or i == 1:
            logger.info(f"{i}. ürün işleniyor: {link}")

        details = get_product_details(link, driver)
        details["Fiyat (TRY)"] = price
        details["Link"] = link
        details["Çekilme Zamanı"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        results.append(details)

    df_detailed = pd.DataFrame(results)
    return df_detailed


def scrape_hepsiburada(base_url: str, total_pages: int):
    os.makedirs(LINK_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    driver = webdriver.Chrome()

    try:
        links_df = get_product_links(base_url, total_pages, driver)
        link_path = os.path.join(
            LINK_DIR, f"HB_Links_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
        )
        links_df.to_csv(link_path, index=False)
        logger.info(f"Linkler kaydedildi: {link_path}")

        details_df = scrape_all_details(links_df, driver)
        raw_path = os.path.join(
            RAW_DIR, f"HB_Details_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
        )
        details_df.to_csv(raw_path, index=False)
        logger.info(f"Detaylar kaydedildi: {raw_path}")

    finally:
        driver.quit()
