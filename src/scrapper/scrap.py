from hepsiburada import scrape_hepsiburada


def main():
    BASE_URL_HB = "https://www.hepsiburada.com/laptop-notebook-dizustu-bilgisayarlar-c-98?puan=3-max&sayfa="
    TOTAL_PAGES_HB = 2
    scrape_hepsiburada(BASE_URL_HB, TOTAL_PAGES_HB)


if __name__ == "__main__":
    main()
