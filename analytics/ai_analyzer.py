import os

import pandas
from dotenv import load_dotenv
from google import genai

from config import ANALYSIS_OUTPUT_FILE, DOU_UA_URL
from logger import logger


load_dotenv()


def analyze_market_with_ai() -> str | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning(
            "Warning: GEMINI_API_KEY is missing from environment or .env file."
        )
        return None

    models = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash",
        "gemini-2.5-flash",
    ]

    client = genai.Client(api_key=api_key)
    data = pandas.read_csv(ANALYSIS_OUTPUT_FILE)
    clean_data = data.head(30).to_string(index=False)
    prompt = (
        "You are an expert tech career advisor. "
        "Analyze the following job market "
        "technology frequencies and provide:\n"
        "1. Concise career advice in exactly 3 simple sentences.\n"
        "2. Top 3 career fields to target based on demand.\n\n"
        f"Data:\n{clean_data}"
        f"\nData source: {DOU_UA_URL}"
    )

    for model in models:
        logger.info(f"Analyzing data with {model} model...")
        try:
            response = client.interactions.create(
                model=model,
                input=prompt,
                timeout=30,
            )
            return response.output_text
        except Exception as e:
            logger.warning(f"Error calling Gemini API: {e}")
            continue

    return None
