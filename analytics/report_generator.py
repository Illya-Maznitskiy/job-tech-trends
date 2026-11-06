from datetime import datetime
import json
import webbrowser
from pathlib import Path

import pandas
from jinja2 import Environment, FileSystemLoader

from analytics.ai_analyzer import analyze_market_with_ai
from config import (
    POSITIONS,
    POSITION_ANALYSIS_OUTPUT_FILE,
    POSITION_SCRAPING_OUTPUT_FILE,
    HTML_PAGE_OUTPUT_FILE,
    TECHNOLOGIES_TO_DISPLAY,
    MEMES_FILE,
)
from logger import logger
from utils import log_line_break, get_position_url

environment = Environment(loader=FileSystemLoader("analytics/templates/"))
template = environment.get_template("index.html")


def get_memes() -> list:
    try:
        with open(MEMES_FILE, encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError) as e:
        logger.warning(f"Memes are not loaded: {e}")
        return []


def get_position_data(position: str, category: str) -> dict:
    counts = pandas.read_csv(
        POSITION_ANALYSIS_OUTPUT_FILE.format(position=position)
    )
    jobs = pandas.read_csv(
        POSITION_SCRAPING_OUTPUT_FILE.format(position=position)
    )

    return {
        "name": position,
        "category": category,
        "total_jobs": len(jobs),
        "scraped_url": get_position_url(category),
        "top_skills": counts.head(3).to_dict("records"),
        "chart_skills": counts.head(TECHNOLOGIES_TO_DISPLAY).to_dict(
            "records"
        ),
        "ai_summary": analyze_market_with_ai(position, category, counts),
    }


def get_report_data() -> dict:
    positions = []
    for position, category in POSITIONS.items():
        try:
            positions.append(get_position_data(position, category))
        except Exception as e:
            # One broken position must not stop the others
            logger.error(f"Report skipped {position}: {e}")

    if not positions:
        raise ValueError("No position data found for the report")

    return {
        "run_date": datetime.now().strftime("%d-%m-%Y"),
        "memes": get_memes(),
        "positions": positions,
        # TEMP: the template still reads one position, until it gets buttons
        **positions[0],
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
