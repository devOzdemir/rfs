from selenium.webdriver.common.by import By
import pandas as pd
import time
from datetime import datetime


def get_product_links(base_url: str, total_pages: int = 1, driver=None) -> pd.DataFrame:
    """
    Hepsiburada'dan ürün başlıklarını, fiyatlarını ve linklerini çeker.
    """
    all_results = []

    for page in range(1, total_pages + 1):
        print(f"[INFO] Processing page {page}...")
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
        time.sleep(1.5)

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
            print(f"[WARN] Başlık veya marka bilgisi alınamadı: {link} - {e}")

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
            print(f"[WARN] Teknik özellikler tablosu bulunamadı: {link} - {e}")

    except Exception as e:
        print(f"[ERROR] Ürün detayları alınamadı: {e}")

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
            print(f"[INFO] {i}. ürün işleniyor: {link}")

        details = get_product_details(link, driver)
        details["Fiyat (TRY)"] = price
        details["Link"] = link
        details["Çekilme Zamanı"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        results.append(details)

    df_detailed = pd.DataFrame(results)
    return df_detailed
