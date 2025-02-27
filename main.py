from analytics import analysis
from scraping import scraper

if __name__ == "__main__":
    print("\n\tStarting Job Technical Trends...\n\t")

    scraper.scrape_jobs()
    analysis.run_analysis()
