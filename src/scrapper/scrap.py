from hepsiburada import scrape_hepsiburada
from trendyol import scrape_trendyol


def main():
    BASE_URL_HB = "https://www.hepsiburada.com/laptop-notebook-dizustu-bilgisayarlar-c-98?puan=3-max&sayfa="
    TOTAL_PAGES_HB = 49

    BASE_URL_TY = "https://www.trendyol.com/sr?wc=103108%2C106084&sst=MOST_RATED"
    TOTAL_PAGES_TY = 98

    scrape_hepsiburada(BASE_URL_HB, TOTAL_PAGES_HB)
    scrape_trendyol(BASE_URL_TY, TOTAL_PAGES_TY)


if __name__ == "__main__":
    main()
