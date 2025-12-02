import os
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)

LINK_DIR = "../../data/link"
RAW_DIR = "../../data/raw"
PROCESSED_DIR = "../../data/processed"

# Use an absolute log folder so logs don't end up in an unexpected CWD
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d%H%M")
log_file = LOG_DIR / f"TY_Scraper_{timestamp}.log"

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

# Dedicated logger to avoid clashing with Hepsiburada (or other modules) in the same process.
logger = logging.getLogger("scrapper.trendyol")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter(LOG_FORMAT)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

# Prevent logs from bubbling up to the root logger (which may have other handlers)
logger.propagate = False

TARGET_FIELDS = [
    # Üst Bilgiler
    "Başlık",
    "Marka",
    # İşlemci Bilgileri
    "İşlemci Tipi",
    "İşlemci Modeli",
    "İşlemci Nesli",
    "İşlemci Çekirdek Sayısı",
    "Temel İşlemci Hızı (GHz)",
    "Maksimum İşlemci Hızı (GHz)",
    # RAM / Bellek Bilgileri
    "Ram (Sistem Belleği)",
    "Ram (Sistem Belleği) Tipi",
    "Arttırılabilir Azami Bellek",
    # Depolama
    "SSD Kapasitesi",
    "Hard Disk Kapasitesi",
    # Ekran Bilgileri
    "Ekran Boyutu",
    "Çözünürlük",
    "Çözünürlük Standartı",
    "Ekran Yenileme Hızı",
    "Panel Tipi",
    # Ekran Kartı Bilgileri
    "Ekran Kartı",
    "Ekran Kartı Tipi",
    "Ekran Kartı Hafızası",
    "Ekran Kartı Bellek Tipi",
    "Ekran Kartı Gücü",
    # Diğer Donanım Özellikleri
    "Cihaz Ağırlığı",
    "Kullanım Amacı",
    "Şarjlı Kullanım Süresi",
    # Yazılım ve Diğer Bilgiler
    "İşletim Sistemi",
    # "Garanti Tipi",
    # "Garanti Süresi",
    # "Menşei",
    "Renk",
    # Meta
    "Çekilme Zamanı",
]


def expand_product_attributes(driver, timeout: int = 10) -> None:
    """Clicks the correct 'Daha Fazla Göster' inside the product attributes container (if present)."""
    wait = WebDriverWait(driver, timeout)

    # Scope clicks to the attributes root to avoid other 'show more' buttons on the page
    root_selector = (
        "div.product-attributes-container.product-attributes, "
        "div[data-drroot='product-attributes']"
    )

    try:
        root = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, root_selector))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", root)

        # The button is usually located under `.show-more-section`
        buttons = root.find_elements(
            By.CSS_SELECTOR, ".show-more-section button.show-more-button"
        )
        if not buttons:
            return

        btn = buttons[0]
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", btn
            )
            # Prefer native click; fallback to JS click when intercepted
            try:
                btn.click()
            except (ElementClickInterceptedException, StaleElementReferenceException):
                driver.execute_script("arguments[0].click();", btn)

            # After clicking, DOM may re-render; briefly wait for either:
            # - the button to disappear, or
            # - more attribute items to become available
            def _expanded(_driver):
                try:
                    current_root = _driver.find_element(By.CSS_SELECTOR, root_selector)
                    item_count = len(
                        current_root.find_elements(
                            By.CSS_SELECTOR, "div.attributes div.attribute-item"
                        )
                    )
                    # heuristic: expanded pages often have more than 12 items
                    return item_count > 12
                except Exception:
                    return True

            wait.until(_expanded)
        except Exception as e:
            logger.warning(
                f"Ürün özellikleri için 'Daha Fazla Göster' tıklanamadı: {e}"
            )

    except TimeoutException:
        logger.warning(
            "Ürün özellikleri kapsayıcı alanı bulunamadı; 'Daha Fazla Göster' tıklanamadı."
        )


def get_product_links_trendyol(base_url: str, total_pages: int, driver):
    all_data = []

    for page in range(1, total_pages + 1):
        url = f"{base_url}&pi={page}"
        logger.info(f"Sayfa {page} işleniyor: {url}")

        try:
            driver.get(url)
            wait = WebDriverWait(driver, 15)
            wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.product-card"))
            )

            product_cards = driver.find_elements(By.CSS_SELECTOR, "a.product-card")
            logger.info(f"{len(product_cards)} ürün bulundu.")

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
                    logger.warning(f"Ürün işlenirken hata: {e}")

        except Exception as e:
            logger.error(f"Sayfa işlenemedi: {e}")
            continue

    df = pd.DataFrame(all_data)
    return df


def get_product_details_trendyol(link: str, driver) -> dict:
    features = {field: None for field in TARGET_FIELDS}
    wait = WebDriverWait(driver, 15)

    try:
        driver.get(link)

        # Başlık ve Marka
        try:
            h1_elem = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.product-title"))
            )
            brand_elem = h1_elem.find_element(By.CSS_SELECTOR, "a strong")
            brand = brand_elem.text.strip()
            title = h1_elem.text.strip().replace(brand, "").strip()
            features["Marka"] = brand
            features["Başlık"] = title
        except Exception as e:
            logger.warning(f"Başlık veya marka alınamadı: {e}")

        # Ürün Özellikleri: önce doğru kapsayıcıyı genişlet
        expand_product_attributes(driver)

        # Özellikler (sadece 'Ürün Özellikleri' bölümünü hedefle)
        try:
            root_selector = (
                "div.product-attributes-container.product-attributes, "
                "div[data-drroot='product-attributes']"
            )
            root = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, root_selector))
            )

            # 'Ürün Özellikleri' başlığı olan section
            feature_section = root.find_element(
                By.XPATH,
                ".//div[contains(@class,'attributes-section')][.//h3[normalize-space()='Ürün Özellikleri']]",
            )
            attr_items = feature_section.find_elements(
                By.CSS_SELECTOR, "div.attributes div.attribute-item"
            )

            for item in attr_items:
                try:
                    label = item.find_element(By.CSS_SELECTOR, ".name").text.strip()
                    value = item.find_element(By.CSS_SELECTOR, ".value").text.strip()

                    if label in features and value:
                        # Aynı etiket gelirse kaybetmemek için birleştir
                        if features[label] and features[label] != value:
                            features[label] = f"{features[label]}; {value}"
                        else:
                            features[label] = value
                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Özellikler okunamadı: {e}")

    except Exception as e:
        logger.error(f"Ürün detayları alınamadı: {e}")

    features["Çekilme Zamanı"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return features


def scrape_all_details_trendyol(links_df: pd.DataFrame, driver) -> pd.DataFrame:
    results = []

    for i, (link, price) in enumerate(
        zip(links_df["Link"], links_df["Price"]), start=1
    ):
        if i % 50 == 0 or i == 1:
            logger.info(f"{i}. ürün işleniyor: {link}")

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
        logger.info(f"Linkler kaydedildi: {link_path}")

        details_df = scrape_all_details_trendyol(links_df, driver)
        raw_path = os.path.join(
            RAW_DIR, f"TY_Details_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
        )
        details_df.to_csv(raw_path, index=False)
        logger.info(f"Detaylar kaydedildi: {raw_path}")

    finally:
        driver.quit()
