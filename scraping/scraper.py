import os
import time

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.internet import defer

from config import POSITIONS, POSITION_SCRAPING_OUTPUT_FILE
from scraping.job_scraping.spiders.douua import DouUaSpider
from logger import logger
from utils import log_line_break

os.environ.setdefault(
    "SCRAPY_SETTINGS_MODULE", "scraping.job_scraping.settings"
)


@defer.inlineCallbacks
def crawl_positions(process):
    # One position at a time, to keep the load on DOU low
    summary = []
    for number, (position, category) in enumerate(POSITIONS.items(), 1):
        logger.info(f"\n\n📌 [{number}/{len(POSITIONS)}] Position: {position}")
        start_time = time.time()
        # Each position writes to its own CSV
        crawler = process.create_crawler(DouUaSpider)
        output_file = POSITION_SCRAPING_OUTPUT_FILE.format(position=position)
        crawler.settings.set(
            "FEEDS",
            {output_file: {"format": "csv", "overwrite": True}},
            priority="spider",
        )
        yield process.crawl(crawler, category=category)
        summary.append(
            f"  {position}: {crawler.spider.scraped_count} jobs, "
            f"{time.time() - start_time:.0f}s"
        )

    logger.info("\n\n✅ Scraping summary:\n" + "\n".join(summary) + "\n")


def scrape_jobs():
    log_line_break()
    logger.info("Starting scraping...")
    settings = get_project_settings()
    process = CrawlerProcess(settings)

    try:
        logger.info("Scraping Dou.ua started...")
        crawl_positions(process)
        process.start()
    except Exception as e:
        logger.error(f"Error during scraping process: {e}")
        exit(1)

    logger.info("Scraping finished.")
