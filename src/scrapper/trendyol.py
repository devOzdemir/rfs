import os
import time
import logging
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By

LINK_DIR = "../../data/link"
RAW_DIR = "../../data/raw"
PROCESSED_DIR = "../../data/processed"

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d%H%M")
log_file = os.path.join(LOG_DIR, f"TY_Scraper_{timestamp}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)

TARGET_FIELDS = [
    # Üst Bilgiler
    "Başlık",
    "Marka",
    "Ürün Modeli",
    # İşlemci Bilgileri
    "İşlemci Tipi",
    "İşlemci",
    "İşlemci Modeli",
    "İşlemci Nesli",
    "İşlemci Cache",
    "İşlemci Çekirdek Sayısı",
    "Temel İşlemci Hızı (GHz)",
    "Maksimum İşlemci Hızı (GHz)",
    # RAM / Bellek Bilgileri
    "Ram (Sistem Belleği)",
    "Ram Tipi",
    "Ram (Sistem Belleği) Tipi",
    "Bellek Hızı",
    "Arttırılabilir Azami Bellek",
    # Depolama
    "SSD Kapasitesi",
    "Hard Disk Kapasitesi",
    "Optik Sürücü Tipi",
    # Ekran Bilgileri
    "Ekran Boyutu",
    "Çözünürlük",
    "Çözünürlük Standartı",
    "Max Ekran Çözünürlüğü",
    "Ekran Yenileme Hızı",
    "Panel Tipi",
    "Dokunmatik Ekran",
    # Ekran Kartı Bilgileri
    "Ekran Kartı",
    "Ekran Kartı Tipi",
    "Ekran Kartı Hafızası",
    "Ekran Kartı Bellek Tipi",
    "Ekran Kartı Gücü",
    # Diğer Donanım Özellikleri
    "Klavye",
    "Cihaz Ağırlığı",
    "Kullanım Amacı",
    "Bağlantılar",
    "Şarjlı Kullanım Süresi",
    "Suya/Toza Dayanıklılık",
    "Hızlı Şarj",
    "Parmak İzi Okuyucu",
    # Yazılım ve Diğer Bilgiler
    "İşletim Sistemi",
    "Garanti Tipi",
    "Garanti Süresi",
    "Menşei",
    "Tamir Edilebilirlik",
    "Renk",
    # Meta
    "Çekilme Zamanı",
]


def get_product_links_trendyol(base_url: str, total_pages: int, driver):
    all_data = []

    for page in range(1, total_pages + 1):
        url = f"{base_url}&pi={page}"
        logging.info(f"Sayfa {page} işleniyor: {url}")

        try:
            driver.get(url)
            time.sleep(3)

            product_cards = driver.find_elements(By.CSS_SELECTOR, "a.product-card")
            logging.info(f"{len(product_cards)} ürün bulundu.")

            for card in product_cards:
                try:
                    brand = card.find_element(
                        By.CLASS_NAME, "product-brand"
                    ).text.strip()
                    name = card.find_element(By.CLASS_NAME, "product-name").text.strip()
                    price_elem = card.find_element(
                        By.CSS_SELECTOR, 'div[data-testid="single-price"]'
                    )
                    href = card.get_attribute("href")

                    title = f"{brand} {name}".strip()
                    price = price_elem.text.strip()
                    link = href

                    all_data.append(
                        {
                            "Name": title,
                            "Price": price,
                            "Link": link,
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )
                except Exception as e:
                    logging.warning(f"Ürün işlenirken hata: {e}")

        except Exception as e:
            logging.error(f"Sayfa işlenemedi: {e}")
            continue

    df = pd.DataFrame(all_data)
    return df


def get_product_details_trendyol(link: str, driver) -> dict:
    features = {field: None for field in TARGET_FIELDS}

    try:
        driver.get(link)
        time.sleep(3)

        # Başlık ve Marka
        try:
            h1_elem = driver.find_element(By.CSS_SELECTOR, "h1.product-title")
            brand_elem = h1_elem.find_element(By.CSS_SELECTOR, "a strong")
            brand = brand_elem.text.strip()
            title = h1_elem.text.strip().replace(brand, "").strip()
            features["Marka"] = brand
            features["Başlık"] = title
        except Exception as e:
            logging.warning(f"Başlık veya marka alınamadı: {e}")

        # Özellikler
        try:
            attr_container = driver.find_element(By.CLASS_NAME, "attributes")
            attr_items = attr_container.find_elements(By.CLASS_NAME, "attribute-item")
            for item in attr_items:
                try:
                    label_elem = item.find_element(By.CLASS_NAME, "name")
                    value_elem = item.find_element(By.CLASS_NAME, "value")
                    label = label_elem.text.strip()
                    value = value_elem.text.strip()
                    if label in features:
                        features[label] = value
                except Exception:
                    continue
        except Exception as e:
            logging.warning(f"Özellikler okunamadı: {e}")

    except Exception as e:
        logging.error(f"Ürün detayları alınamadı: {e}")

    features["Çekilme Zamanı"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return features


def scrape_all_details_trendyol(links_df: pd.DataFrame, driver) -> pd.DataFrame:
    results = []

    for i, (link, price) in enumerate(
        zip(links_df["Link"], links_df["Price"]), start=1
    ):
        if i % 50 == 0 or i == 1:
            logging.info(f"{i}. ürün işleniyor: {link}")

        details = get_product_details_trendyol(link, driver)
        details["Fiyat (TRY)"] = price
        details["Link"] = link
        results.append(details)

    df = pd.DataFrame(results)
    return df


def scrape_trendyol(base_url: str, total_pages: int):
    os.makedirs(LINK_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    driver = webdriver.Chrome()

    try:
        links_df = get_product_links_trendyol(base_url, total_pages, driver)
        link_path = os.path.join(
            LINK_DIR, f"TY_Links_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
        )
        links_df.to_csv(link_path, index=False)
        logging.info(f"Linkler kaydedildi: {link_path}")

        details_df = scrape_all_details_trendyol(links_df, driver)
        raw_path = os.path.join(
            RAW_DIR, f"TY_Details_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
        )
        details_df.to_csv(raw_path, index=False)
        logging.info(f"Detaylar kaydedildi: {raw_path}")

    finally:
        driver.quit()
