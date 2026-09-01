import logging
import sys
import os

from config import LOGGER_LEVEL

os.makedirs("logs", exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")

logging.getLogger("scrapy").propagate = False
logging.getLogger("WDM").setLevel(logging.WARNING)

logging.getLogger("matplotlib").setLevel(LOGGER_LEVEL)
logging.getLogger("asyncio").setLevel(LOGGER_LEVEL)
logging.getLogger("selenium").setLevel(LOGGER_LEVEL)
logging.getLogger("urllib3").setLevel(LOGGER_LEVEL)
logging.getLogger("PIL").setLevel(LOGGER_LEVEL)


logging.basicConfig(
    level=LOGGER_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/scraper.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("scraper")
