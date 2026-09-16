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


def visualize_jobs() -> None:
    log_line_break()
    logger.info("Starting visualization...")

    if not os.path.exists(ANALYSIS_OUTPUT_FILE):
        logger.error(f"Analysis file not found at: {ANALYSIS_OUTPUT_FILE}")
        return
    tech_counts = pd.read_csv(ANALYSIS_OUTPUT_FILE).head(
        TECHNOLOGIES_TO_DISPLAY
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_facecolor("#D9D9D9")
    plt.bar(
        tech_counts["Technology"],
        tech_counts["Count"],
        color=plt.cm.ocean(tech_counts["Count"] / tech_counts["Count"].max()),
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

    logger.info("Finished visualization.")
    log_line_break()

    plt.show()
