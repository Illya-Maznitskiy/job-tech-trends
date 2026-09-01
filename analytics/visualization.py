import os

import pandas as pd
import matplotlib.pyplot as plt

from config import (
    ANALYSIS_OUTPUT_FILE,
    VISUALIZATION_OUTPUT_FILE,
    TECHNOLOGIES_TO_DISPLAY,
)
from logger import logger
from utils import log_line_break


def plot_tech_counts(analysis_output_file: str) -> None:
    tech_counts = pd.read_csv(analysis_output_file)
    top_tech_counts = tech_counts.sort_values(
        by="Count", ascending=False
    ).head(TECHNOLOGIES_TO_DISPLAY)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor("#D9D9D9")
    plt.bar(
        top_tech_counts["Technology"],
        top_tech_counts["Count"],
        color=plt.cm.ocean(
            top_tech_counts["Count"] / top_tech_counts["Count"].max()
        ),
    )

    plt.title(
        f"Top {TECHNOLOGIES_TO_DISPLAY} Technology Counts in Job Descriptions"
    )
    plt.xlabel("Technology")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha="right")

    os.makedirs(os.path.dirname(VISUALIZATION_OUTPUT_FILE), exist_ok=True)
    plt.tight_layout()
    plt.savefig(VISUALIZATION_OUTPUT_FILE)
    logger.info(f"Plot saved to {VISUALIZATION_OUTPUT_FILE}")

    plt.show()


def visualize_jobs():
    log_line_break()
    logger.info("\nStarting visualization...\n")

    plot_tech_counts(ANALYSIS_OUTPUT_FILE)

    logger.info("\nFinished visualization.\n")
