from datetime import datetime
import webbrowser
from pathlib import Path

import pandas
from jinja2 import Environment, FileSystemLoader

from analytics.ai_analyzer import analyze_market_with_ai
from config import (
    DOU_UA_URL,
    ANALYSIS_OUTPUT_FILE,
    SCRAPING_OUTPUT_FILE,
    HTML_PAGE_OUTPUT_FILE,
    VISUALIZATION_OUTPUT_FILE,
)
from logger import logger
from utils import log_line_break

environment = Environment(loader=FileSystemLoader("analytics/templates/"))
template = environment.get_template("index.html")


def get_report_data() -> dict:
    output_data = pandas.read_csv(ANALYSIS_OUTPUT_FILE)

    total_jobs = len(pandas.read_csv(SCRAPING_OUTPUT_FILE))
    run_date = datetime.now().strftime("%d-%m-%Y")
    scraped_url = DOU_UA_URL
    top_skill = output_data.iloc[0]["Technology"]
    top_skill_count = output_data.iloc[0]["Count"]
    ai_summary = analyze_market_with_ai()
    plot_filename = Path(VISUALIZATION_OUTPUT_FILE).name

    return {
        "total_jobs": total_jobs,
        "run_date": run_date,
        "scraped_url": scraped_url,
        "top_skill": top_skill,
        "top_skill_count": top_skill_count,
        "ai_summary": ai_summary,
        "plot_filename": plot_filename,
    }


def generate_report() -> None:
    log_line_break()
    logger.info("Generating report...")

    try:
        rendered_html = template.render(get_report_data())

        with open(HTML_PAGE_OUTPUT_FILE, "w", encoding="utf-8") as file:
            file.write(rendered_html)

        webbrowser.open(Path(HTML_PAGE_OUTPUT_FILE).resolve().as_uri())
        logger.info(f"Success, {HTML_PAGE_OUTPUT_FILE} has been created.")

    except Exception as e:
        logger.error(e)
