import logging
import os

import matplotlib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from config import ANALYSIS_OUTPUT_FILE


matplotlib.use("TkAgg")
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)


def plot_tech_counts(csv_path):
    tech_counts = pd.read_csv(csv_path)
    top_tech_counts = tech_counts.sort_values(
        by="Count", ascending=False
    ).head(20)

    plt.figure(figsize=(10, 6))

    sns.barplot(
        data=top_tech_counts, x="Technology", y="Count", palette="viridis"
    )

    plt.title("Top 20 Technology Counts in Python Job Descriptions")
    plt.xlabel("Technology")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha="right")

    output_image_path = "analytics/data/tech_counts_plot.png"
    os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_image_path)
    print(f"Plot saved to {output_image_path}")

    plt.show()


def visualize_jobs():
    print("\nStarting visualization...\n")

    plot_tech_counts(ANALYSIS_OUTPUT_FILE)

    print("\nFinished visualization.\n")


if __name__ == "__main__":
    visualize_jobs()
