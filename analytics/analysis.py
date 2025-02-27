import csv
import os
import re
import pandas as pd
import nltk
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download("stopwords")
nltk.download("punkt")

STOPWORDS = set(stopwords.words("english"))

TECHNOLOGIES = [
    "Python",
    "Django",
    "Flask",
    "AWS",
    "Kubernetes",
    "TensorFlow",
    "PyTorch",
    "SQL",
    "PostgreSQL",
    "Docker",
]


def load_data(folder_path):
    job_descriptions = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".csv"):
            with open(
                os.path.join(folder_path, file_name), "r", encoding="utf-8"
            ) as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if "description" in row and row["description"].strip():
                        job_descriptions.append(row["description"])
    return job_descriptions


def preprocess_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    words = word_tokenize(text)
    words = [word for word in words if word not in STOPWORDS]
    return words


def count_technologies(job_descriptions):
    word_counts = Counter()

    for desc in job_descriptions:
        words = preprocess_text(desc)
        word_counts.update(words)

    tech_frequencies = {
        tech: word_counts[tech.lower()]
        for tech in TECHNOLOGIES
        if tech.lower() in word_counts
    }
    return tech_frequencies


def save_results(counts, output_path):
    df = pd.DataFrame(counts.items(), columns=["Technology", "Count"])
    df.sort_values(by="Count", ascending=False, inplace=True)
    df.to_csv(output_path, index=False)

    last_few_dirs = os.path.normpath(output_path).split(os.sep)[-4:]
    last_few_dirs_str = os.sep.join(last_few_dirs)
    print(f"Results saved to {last_few_dirs_str}")


def run_analysis():
    print("\nStarting analysis...\n")

    current_script_dir = os.path.dirname(os.path.realpath(__file__))

    data_folder = os.path.join(current_script_dir, "../scraping/data/")
    absolute_data_path = os.path.abspath(data_folder)

    if not os.path.exists(absolute_data_path):
        print(f"Checking data folder path: {absolute_data_path}")
        print("ERROR: Data folder does not exist!")
        return
    else:
        print("Data folder found, proceeding...")

    output_folder = os.path.join(current_script_dir, "data")

    if not os.path.exists(output_folder):
        print(f"Checking output folder path: {output_folder}")
        print("ERROR: Output folder does not exist! Creating it...")
        os.makedirs(output_folder)
    else:
        print("Output folder found, proceeding...")

    output_file = os.path.join(output_folder, "tech_counts.csv")
    descriptions = load_data(absolute_data_path)
    tech_counts = count_technologies(descriptions)

    save_results(tech_counts, output_file)

    print("\n Analysing finished\n")


if __name__ == "__main__":
    run_analysis()
