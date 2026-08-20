import logging
import sys
import os


os.makedirs("logs", exist_ok=True)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/scraper.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("scraper")
