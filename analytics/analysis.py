import csv
import os
import re
from pathlib import Path

import pandas as pd
import nltk
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from config import TECHNOLOGIES_TO_ANALYZE
from logger import logger
from utils import log_line_break

nltk.download("stopwords")
nltk.download("punkt")
nltk.download("punkt_tab")

STOPWORDS = set(stopwords.words("english"))


def load_data(folder_path):
    return [
        row["description"]
        for file in Path(folder_path).glob("*.csv")
        for row in csv.DictReader(open(file, "r", encoding="utf-8"))
        if "description" in row and row["description"].strip()
    ]


def preprocess_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    words = word_tokenize(text)
    words = [word for word in words if word not in STOPWORDS]
    return words


def count_technologies(job_descriptions):
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


def save_results(counts, output_path):
    df = pd.DataFrame(counts.items(), columns=["Technology", "Count"])
    df.sort_values(by="Count", ascending=False, inplace=True)
    df.to_csv(output_path, index=False)

    last_few_dirs = os.path.normpath(output_path).split(os.sep)[-3:]
    last_few_dirs_str = os.sep.join(last_few_dirs)
    logger.info(f"Results saved to {last_few_dirs_str}")


def analyze_technologies():
    log_line_break()
    logger.info("\nStarting analysis...\n")

    current_script_dir = os.path.dirname(os.path.realpath(__file__))

    data_folder = os.path.join(current_script_dir, "../scraping/data/")
    absolute_data_path = os.path.abspath(data_folder)

    logger.info(f"Checking data folder path: {absolute_data_path}")
    if not os.path.exists(absolute_data_path):
        logger.error("Data folder does not exist!")
        return
    logger.info("Data folder found, proceeding...")

    output_folder = os.path.join(current_script_dir, "data")

    logger.info(f"Checking output folder path: {output_folder}")
    if not os.path.exists(output_folder):
        logger.info("Output folder does not exist! Creating it...")
        os.makedirs(output_folder)
    logger.info("Output folder found, proceeding...")

    output_file = os.path.join(output_folder, "tech_counts.csv")
    descriptions = load_data(absolute_data_path)
    tech_counts = count_technologies(descriptions)

    save_results(tech_counts, output_file)

    logger.info("\nAnalysing finished.\n")


if __name__ == "__main__":
    analyze_technologies()
