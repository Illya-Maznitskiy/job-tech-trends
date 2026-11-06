from urllib.parse import quote, urlencode

from config import DOU_UA_BASE_URL
from logger import logger


def log_line_break():
    logger.info("=" * 50)


def get_position_url(category: str) -> str:
    query = urlencode({"category": category}, quote_via=quote)
    return f"{DOU_UA_BASE_URL}?{query}"
