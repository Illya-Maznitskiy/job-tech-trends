import csv
import os
import re
from pathlib import Path

import pandas as pd
import nltk
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from config import (
    TECHNOLOGIES_TO_ANALYZE,
    SCRAPING_OUTPUT_FILE,
    ANALYSIS_OUTPUT_FILE,
)
from logger import logger
from utils import log_line_break

nltk.download("stopwords")
nltk.download("punkt")
nltk.download("punkt_tab")

STOPWORDS = set(stopwords.words("english"))


def get_job_descriptions(folder_path: str) -> list[str]:
    return [
        row["description"]
        for file in Path(folder_path).glob("*.csv")
        for row in csv.DictReader(open(file, "r", encoding="utf-8"))
        if "description" in row and row["description"].strip()
    ]


def preprocess_text(text: str) -> list[str]:
    # Clean text: remove noise/punctuation but keep words,
    # spaces, and tech symbols (+, #, ., /, -)
    text = re.sub(r"[^\w\s+#./-]", "", text.lower())

    # Convert text into a list of words using smart linguistic rules
    words = word_tokenize(text)
    return [word for word in words if word not in STOPWORDS and word != "."]


def count_technologies(job_descriptions: list[str]) -> dict[str, int]:
    word_counts = Counter()

    for desc in job_descriptions:
        words = set(preprocess_text(desc))
        word_counts.update(words)

    tech_frequencies = {
        tech: word_counts[tech.lower()]
        for tech in TECHNOLOGIES_TO_ANALYZE
        if tech.lower() in word_counts
    }
    return tech_frequencies


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
