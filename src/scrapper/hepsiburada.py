from selenium.webdriver.common.by import By
import pandas as pd
import time
from datetime import datetime
import os
import logging
from selenium import webdriver

LINK_DIR = "../../data/link"
RAW_DIR = "../../data/raw"
PROCESSED_DIR = "../../data/processed"

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d%H%M")
log_file = os.path.join(LOG_DIR, f"HB_Scraper_{timestamp}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # Terminale log
        logging.FileHandler(log_file, encoding="utf-8"),  # Dosyaya log
    ],
)


def get_product_links(base_url: str, total_pages: int = 1, driver=None) -> pd.DataFrame:
    """
    Hepsiburada'dan ürün başlıklarını, fiyatlarını ve linklerini çeker.
    """
    all_results = []

    for page in range(1, total_pages + 1):
        logging.info(f"Processing page {page}...")
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
    target_fields = [
        "Başlık",
        "Marka",
        "Ürün Modeli",
        "İşlemci Tipi",
        "İşlemci",
        "İşlemci Nesli",
        "İşlemci Cache",
        "Maksimum İşlemci Hızı",
        "Ram Tipi",
        "Ram (Sistem Belleği)",
        "Bellek Hızı",
        "Ekran Kartı Tipi",
        "Ekran Kartı",
        "Ekran Kartı Bellek Tipi",
        "Ekran Kartı Hafızası",
        "SSD Kapasitesi",
        "Harddisk Kapasitesi",
        "Ekran Panel Tipi",
        "Max Ekran Çözünürlüğü",
        "Ekran Boyutu",
        "Ekran Yenileme Hızı",
        "İşletim Sistemi",
    ]

    features = {field: None for field in target_fields}

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
            logging.warning(f"Başlık veya marka bilgisi alınamadı: {link} - {e}")

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

                    if label in features:
                        features[label] = value

                except Exception:
                    continue

        except Exception as e:
            logging.warning(f"Teknik özellikler tablosu bulunamadı: {link} - {e}")

    except Exception as e:
        logging.error(f"Ürün detayları alınamadı: {e}")

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
            logging.info(f"{i}. ürün işleniyor: {link}")

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
        logging.info(f"Linkler kaydedildi: {link_path}")

        details_df = scrape_all_details(links_df, driver)
        raw_path = os.path.join(
            RAW_DIR, f"HB_Details_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
        )
        details_df.to_csv(raw_path, index=False)
        logging.info(f"Detaylar kaydedildi: {raw_path}")

    finally:
        driver.quit()
