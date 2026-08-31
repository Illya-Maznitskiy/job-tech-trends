import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from scraping.job_scraping.spiders.douua import DouUaSpider
from logger import logger
from utils import log_line_break

os.environ.setdefault(
    "SCRAPY_SETTINGS_MODULE", "scraping.job_scraping.settings"
)


def scrape_jobs():
    log_line_break()
    logger.info("\nStarting scraping...\n")
    settings = get_project_settings()
    process = CrawlerProcess(settings)

    try:
        logger.info("Scraping Dou.ua started...")
        process.crawl(DouUaSpider)
        process.start()
    except Exception as e:
        logger.error(f"Error during scraping process: {e}")
        exit(1)

    logger.info("\nScraping finished.\n")
    log_line_break()
