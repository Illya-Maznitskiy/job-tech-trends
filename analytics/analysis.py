import csv
import os
import re
from pathlib import Path

import pandas as pd
from collections import Counter

from config import (
    TECHNOLOGIES_TO_ANALYZE,
    SCRAPING_OUTPUT_FILE,
    ANALYSIS_OUTPUT_FILE,
)
from logger import logger
from utils import log_line_break


def get_job_descriptions(folder_path: str) -> list[str]:
    return [
        row["description"]
        for file in Path(folder_path).glob("*.csv")
        for row in csv.DictReader(open(file, "r", encoding="utf-8"))
        if "description" in row and row["description"].strip()
    ]


def count_technologies(job_descriptions: list[str]) -> dict[str, int]:
    word_counts = Counter()

    for desc in job_descriptions:
        desc_lower = desc.lower()
        vacancy_techs = set()

        for base_name_tech, aliases in TECHNOLOGIES_TO_ANALYZE.items():
            for alias in aliases:
                pattern = (
                    r"(?<![a-z0-9/-])"
                    + re.escape(alias.lower())
                    + r"(?![a-z0-9/-])"
                )
                if re.search(pattern, desc_lower):
                    vacancy_techs.add(base_name_tech)
                    break  # Count tech ONCE per job

        word_counts.update(vacancy_techs)

    return {tech: count for tech, count in word_counts.items() if count > 0}


def save_results(counts: dict[str:int], output_path: str) -> None:
    df = pd.DataFrame(counts.items(), columns=["Technology", "Count"])
    df.sort_values(by="Count", ascending=False, inplace=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")


def analyze_technologies() -> None:
    log_line_break()
    logger.info("\nStarting analysis...\n")

    if not os.path.exists(SCRAPING_OUTPUT_FILE):
        logger.error(f"Scraped data file not found at: {SCRAPING_OUTPUT_FILE}")
        return

    os.makedirs(os.path.dirname(ANALYSIS_OUTPUT_FILE), exist_ok=True)
    descriptions = get_job_descriptions(os.path.dirname(SCRAPING_OUTPUT_FILE))
    tech_counts = count_technologies(descriptions)

    save_results(tech_counts, ANALYSIS_OUTPUT_FILE)

    logger.info("\nAnalysing finished.\n")
