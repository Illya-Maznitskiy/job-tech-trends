from analytics import analysis, visualization
from scraping import scraper


if __name__ == "__main__":
    print("\n\tStarting Job Technical Trends...")

    scraper.scrape_jobs()
    analysis.analyze_technologies()
    visualization.visualize_jobs()

    print("\n\tJob Technical Trends Completed")
