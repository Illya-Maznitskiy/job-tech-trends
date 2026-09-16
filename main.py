from analytics import analysis, visualization
from scraping import scraper
from logger import logger

if __name__ == "__main__":
    logger.info("Starting Job Technical Trends...")

    scraper.scrape_jobs()
    analysis.analyze_technologies()
    visualization.visualize_jobs()
    logger.info("Job Technical Trends Completed")
