import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from scraping.job_scraping.spiders.douua import DouuaSpider
from logger import logger
from config import SCRAPING_OUTPUT_FILE
from utils import log_line_break

os.environ.setdefault(
    "SCRAPY_SETTINGS_MODULE", "scraping.job_scraping.settings"
)


def scrape_jobs():
    log_line_break()
    logger.info("\nStarting scraping...\n")

    if os.path.exists(SCRAPING_OUTPUT_FILE):
        logger.info(
            f"{SCRAPING_OUTPUT_FILE} "
            f"exists. Deleting the file to overwrite it..."
        )
        try:
            os.remove(SCRAPING_OUTPUT_FILE)
        except OSError as e:
            logger.error(f"Error deleting {SCRAPING_OUTPUT_FILE}: {e}")
            exit(1)

    settings = get_project_settings()
    process = CrawlerProcess(settings)

    try:
        logger.info("Scraping Dou.ua started...")
        process.crawl(DouuaSpider)
        process.start()
    except Exception as e:
        logger.error(f"Error during scraping process: {e}")
        exit(1)

    logger.info("\nScraping finished.\n")
    log_line_break()


if __name__ == "__main__":
    scrape_jobs()
