import os
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


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
    # "Ürün Modeli",
    "Kullanım Amacı",
    "Renk",
    "Cihaz Ağırlığı",
    # İşlemci
    "İşlemci Tipi",
    "İşlemci",
    "İşlemci Nesli",
    "İşlemci Çekirdek Sayısı",
    # "İşlemci Cache",
    "Maksimum İşlemci Hızı",
    # Bellek / RAM
    "Ram (Sistem Belleği)",
    "Ram Tipi",
    # "Bellek Hızı",
    # Grafik / GPU
    "Ekran Kartı",
    "Ekran Kartı Tipi",
    # "Ekran Kartı İşlemcisi",
    "Ekran Kartı Hafızası",
    "Ekran Kartı Bellek Tipi",
    # Depolama
    "SSD Kapasitesi",
    "Harddisk Kapasitesi",
    # Ekran
    "Ekran Boyutu",
    "Max Ekran Çözünürlüğü",
    "Ekran Özelliği",
    "Ekran Yenileme Hızı",
    "Ekran Panel Tipi",
    # Yazılım
    "İşletim Sistemi",
]


def _wait_dom_interactive(driver, timeout: int = 10) -> None:
    """Wait until the DOM is at least interactive (fast) so selectors become available."""
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState")
        in ("interactive", "complete")
    )


def wait_for_tech_specs_with_scroll(driver, timeout: int = 20):
    """Hepsiburada sometimes lazy-loads #techSpecs until user scrolls.

    Some product pages contain long brochure/marketing blocks. Large scroll jumps may
    skip the lazy-load trigger, so we:
      1) Try to jump via in-page links (if present)
      2) If #techSpecs exists, scroll it into view directly
      3) Otherwise scroll in smaller steps until it appears

    No time.sleep is used.
    """
    _wait_dom_interactive(driver, timeout=min(10, timeout))

    wait = WebDriverWait(driver, timeout, poll_frequency=0.35)

    def _try_jump_to_specs(d) -> None:
        """Some pages have a shortcut/tab that jumps to tech specs."""
        candidates = []
        # Common patterns: anchor to #techSpecs or a tab/button text
        candidates.extend(d.find_elements(By.CSS_SELECTOR, "a[href='#techSpecs']"))
        candidates.extend(
            d.find_elements(
                By.XPATH,
                "//a[contains(., 'Teknik') and contains(., 'Özellik')] | "
                "//button[contains(., 'Teknik') and contains(., 'Özellik')]",
            )
        )
        if not candidates:
            return

        el = candidates[0]
        try:
            d.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            try:
                el.click()
            except Exception:
                d.execute_script("arguments[0].click();", el)
        except Exception:
            return

    # Small initial scroll: triggers many lazy-load observers without big jumps
    driver.execute_script("window.scrollTo(0, 250);")

    scroll_step = 350

    def _cond(d):
        # If techSpecs already exists, scroll directly to it and return
        try:
            el = d.find_element(By.ID, "techSpecs")
            d.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            return el
        except NoSuchElementException:
            pass

        # Try to use in-page navigation shortcuts (if any)
        _try_jump_to_specs(d)

        # Check again after possible jump
        try:
            el = d.find_element(By.ID, "techSpecs")
            d.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            return el
        except NoSuchElementException:
            pass

        # Otherwise, scroll gradually to avoid skipping lazy-load triggers
        try:
            max_h = d.execute_script("return document.body.scrollHeight")
            y = d.execute_script("return window.pageYOffset")
        except Exception:
            max_h = None
            y = None

        # If we can read offsets, stop near bottom; else just scrollBy
        if max_h is not None and y is not None:
            if y >= max_h - 350:
                # near bottom; one last attempt will be made on next poll
                return False
            d.execute_script(
                "window.scrollTo(0, arguments[0]);",
                min(y + scroll_step, max_h - 200),
            )
        else:
            d.execute_script("window.scrollBy(0, arguments[0]);", scroll_step)

        return False

    return wait.until(_cond)


def get_product_links(base_url: str, total_pages: int = 1, driver=None) -> pd.DataFrame:
    """Hepsiburada'dan ürün başlıklarını, fiyatlarını ve linklerini çeker."""
    all_results = []

    for page in range(1, total_pages + 1):
        logger.info(f"Processing page {page}...")
        driver.get(base_url + str(page))

        wait = WebDriverWait(driver, 15)
        # Wait until at least one price element is present on the listing
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-test-id^='final-price']")
            )
        )

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

    return pd.DataFrame(all_results)


def get_product_details(link: str, driver) -> dict:
    """Tek bir ürünün detay özelliklerini çeker."""
    features = {field: None for field in TARGET_FIELDS}

    try:
        driver.get(link)
        _wait_dom_interactive(driver, timeout=10)
        wait = WebDriverWait(driver, 15)

        try:
            title_element = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[data-test-id="title"]')
                )
            )
            brand_element = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[data-test-id="brand"]')
                )
            )

            features["Başlık"] = title_element.text.strip()
            features["Marka"] = brand_element.get_attribute("title").strip()

        except Exception as e:
            logger.warning(f"Başlık veya marka bilgisi alınamadı: {link} - {e}")

        try:
            tech_specs = wait_for_tech_specs_with_scroll(driver, timeout=20)
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
            logger.warning(
                f"Teknik özellikler tablosu bulunamadı (lazy-load olabilir): {link} - {e}"
            )

    except Exception as e:
        logger.error(f"Ürün detayları alınamadı: {e}")

    features["Çekilme Zamanı"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return features


def scrape_all_details(links_df: pd.DataFrame, driver) -> pd.DataFrame:
    """Ürün linkleri DataFrame'inden tüm ürün detaylarını döndüren DataFrame'i oluşturur."""
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

    return pd.DataFrame(results)


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
