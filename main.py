from analytics import analysis, report_generator
from scraping import scraper
from logger import logger

if __name__ == "__main__":
    logger.info("Starting Job Technical Trends...")

    scraper.scrape_jobs()
    analysis.analyze_technologies()
    report_generator.generate_report()
    logger.info("Job Technical Trends Completed")
