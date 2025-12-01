import os
import logging
from hepsiburada import get_product_links, scrape_all_details
from datetime import datetime
from selenium import webdriver

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d%H%M")
log_file = os.path.join(LOG_DIR, f"scraper_{timestamp}.log")

# Log ayarları
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # Terminale log
        logging.FileHandler(log_file, encoding="utf-8"),  # Dosyaya log
    ],
)

# Kaydetme dizinleri
LINK_DIR = "../../data/link"
RAW_DIR = "../../data/raw"
PROCESSED_DIR = "../../data/processed"

# URL ve sayfa bilgileri
BASE_URL = "https://www.hepsiburada.com/laptop-notebook-dizustu-bilgisayarlar-c-98?puan=3-max&sayfa="
TOTAL_PAGES = 1  # İsteğe göre artırılabilir test icin 1 olarak bırakıldı, max 49 olabilir hepsiburada için


def scrape_hepsiburada():
    logging.info("🔍 Ürün listesi çekiliyor...")

    driver = webdriver.Chrome()

    try:
        links_df = get_product_links(BASE_URL, TOTAL_PAGES, driver)
        os.makedirs(LINK_DIR, exist_ok=True)
        raw_path = os.path.join(LINK_DIR, f"hepsiburada_links_{timestamp}.xlsx")
        links_df.to_excel(raw_path, index=False)
        logging.info(
            f"✅ Ürün bağlantıları {raw_path} dosyasına kaydedildi. Toplam: {len(links_df)} ürün"
        )

    except Exception as e:
        logging.error(f"❌ Ürün linkleri alınırken hata oluştu: {e}")
        driver.quit()
        return

    logging.info("🔎 Ürün detayları çekiliyor...")

    try:
        detailed_df = scrape_all_details(links_df, driver)
        os.makedirs(RAW_DIR, exist_ok=True)
        processed_path = os.path.join(RAW_DIR, f"hepsiburada_details_{timestamp}.xlsx")
        detailed_df.to_excel(processed_path, index=False)
        logging.info(
            f"✅ Ürün detayları {processed_path} dosyasına kaydedildi. Toplam: {len(detailed_df)} ürün"
        )

    except Exception as e:
        logging.error(f"❌ Ürün detayları alınırken hata oluştu: {e}")

    driver.quit()
    print("✅ Hepsiburada scraping işlemi tamamlandı.")


def main():
    scrape_hepsiburada()
    # scrape_trendyol()  # ileride eklenecek


if __name__ == "__main__":
    main()
