import time
import logging
import pandas as pd
from datetime import datetime
from selenium.webdriver.common.by import By

BASE_URL = "https://www.trendyol.com/sr?wc=103108%2C106084"
DOMAIN = "https://www.trendyol.com"


def get_product_links_trendyol(pages, driver):
    all_data = []

    for page in range(1, pages + 1):
        url = f"{BASE_URL}&pi={page}"
        logging.info(f"🔄 Sayfa {page} işleniyor: {url}")
        try:
            driver.get(url)
            time.sleep(3)

            product_cards = driver.find_elements(By.CSS_SELECTOR, "a.product-card")
            logging.info(f"🔗 {len(product_cards)} ürün bulundu.")

            for card in product_cards:
                try:
                    title_elem = card.find_element(By.CLASS_NAME, "product-name")
                    brand_elem = card.find_element(By.CLASS_NAME, "product-brand")
                    price_elem = card.find_element(
                        By.CSS_SELECTOR, 'div[data-testid="single-price"]'
                    )
                    href = card.get_attribute("href")

                    title = f"{brand_elem.text} {title_elem.text}".strip()
                    price = price_elem.text.strip()
                    link = DOMAIN + href if href.startswith("/") else href

                    all_data.append(
                        {
                            "title": title,
                            "price": price,
                            "link": link,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )
                except Exception as e:
                    logging.warning(f"⛔ Ürün işlenirken hata: {e}")

        except Exception as e:
            logging.error(f"❌ Sayfa işlenemedi: {e}")
            continue

    return pd.DataFrame(all_data)
