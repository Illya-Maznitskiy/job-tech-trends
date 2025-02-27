import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scraping.job_scraping.spiders.douua import DouuaSpider

from config import SCRAPING_OUTPUT_FILE


os.environ.setdefault(
    "SCRAPY_SETTINGS_MODULE", "scraping.job_scraping.settings"
)


def scrape_jobs():
    print("\nStarting scraping...\n")

    if os.path.exists(SCRAPING_OUTPUT_FILE):
        print(
            f"{SCRAPING_OUTPUT_FILE} "
            f"exists. Deleting the file to overwrite it..."
        )
        try:
            os.remove(SCRAPING_OUTPUT_FILE)
        except OSError as e:
            print(f"Error deleting {SCRAPING_OUTPUT_FILE}: {e}")
            exit(1)

    settings = get_project_settings()
    process = CrawlerProcess(settings)

    try:
        print("Scraping Dou.ua started...")
        process.crawl(DouuaSpider)
        process.start()
    except Exception as e:
        print(f"Error during scraping process: {e}")
        exit(1)

    print("\n Scraping finished.\n")


if __name__ == "__main__":
    scrape_jobs()
