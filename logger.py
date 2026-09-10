import logging
import sys
import os
from logging.handlers import RotatingFileHandler

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


file_handler = RotatingFileHandler(
    "logs/scraper.log",
    mode="a",
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
    encoding="utf-8",
)

console_handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[file_handler, console_handler],
    force=True,
)

logger = logging.getLogger("scraper")
