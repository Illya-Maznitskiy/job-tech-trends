import json
from unittest.mock import patch, MagicMock

import pytest
import scrapy
from scrapy.http import HtmlResponse, TextResponse

from config import PROGRESS_LOG_EVERY
from scraping.job_scraping.spiders.douua import DouUaSpider
from scraping.scraper import scrape_jobs


def test_dou_clean_text():
    assert (
        DouUaSpider.clean_text("  Python \xa0 Developer  ")
        == "Python Developer"
    )
    assert DouUaSpider.clean_text(None) == ""
    assert (
        DouUaSpider.clean_text("\n\t Senior   Backend \n") == "Senior Backend"
    )


def test_dou_get_jobs_data_html_response():
    html = """
    <html>
        <body>
            <li class="l-vacancy"><a class="vt"
            href="https://jobs.dou.ua/vacancies/1/">Python Dev</a></li>
        </body>
    </html>
    """
    response = HtmlResponse(
        url="https://jobs.dou.ua/vacancies/", body=html, encoding="utf-8"
    )
    jobs = DouUaSpider.get_jobs_data(response)
    assert len(jobs) == 1


def test_dou_get_jobs_data_json_xhr_response():
    json_data = {
        "html": '<li class="l-vacancy"><a class="vt" '
        'href="https://jobs.dou.ua/vacancies/2/">AWS Dev</a></li>'
    }
    response = TextResponse(
        url="https://jobs.dou.ua/vacancies/xhr-load/",
        body=json.dumps(json_data),
        encoding="utf-8",
    )
    jobs = DouUaSpider.get_jobs_data(response)
    assert len(jobs) == 1


def test_dou_parse_yields_requests_and_pagination():
    spider = DouUaSpider()
    html = """
    <html>
        <body>
            <script>window.CSRF_TOKEN = "test_csrf_token_123";</script>
            <li class="l-vacancy">
                <a class="vt"
                href="https://jobs.dou.ua/vacancies/100/">Python Engineer</a>
                <a class="company">TechCorp</a>
            </li>
        </body>
    </html>
    """
    req = scrapy.Request(url="https://jobs.dou.ua/vacancies/")
    response = HtmlResponse(
        url="https://jobs.dou.ua/vacancies/",
        body=html,
        encoding="utf-8",
        request=req,
    )
    results = list(spider.parse(response))

    # Should yield a vacancy request and a job request
    assert len(results) == 2

    detail_req = results[0]
    assert detail_req.url == "https://jobs.dou.ua/vacancies/100/"
    assert detail_req.meta["title"] == "Python Engineer"
    assert detail_req.meta["company_name"] == "TechCorp"

    form_req = results[1]
    assert "xhr-load" in form_req.url
    assert form_req.meta["csrf_token"] == "test_csrf_token_123"


def test_dou_parse_job_details():
    spider = DouUaSpider()
    html = """
    <html>
        <body>
            <div class="b-typo vacancy-section">
                <p>Looking for a Python Developer \xa0 with
                 Django experience.</p>
                <ul>
                    <li>Must know Docker.</li>
                </ul>
            </div>
            <span class="place bi bi-geo-alt-fill">Kyiv</span>
            <div class="date">14 September 2026</div>
        </body>
    </html>
    """
    response = HtmlResponse(
        url="https://jobs.dou.ua/vacancies/100/",
        body=html,
        encoding="utf-8",
        request=scrapy.Request(
            url="https://jobs.dou.ua/vacancies/100/",
            meta={
                "title": "  Python Engineer  ",
                "company_name": "  TechCorp  ",
            },
        ),
    )

    item = next(spider.parse_job_details(response))

    assert item["title"] == "Python Engineer"
    assert item["company_name"] == "TechCorp"
    assert (
        "Looking for a Python Developer with Django experience."
        " Must know Docker." in item["description"]
    )
    assert item["location"] == "Kyiv"
    assert item["date_posted"] == "14 September 2026"
    assert item["url"] == "https://jobs.dou.ua/vacancies/100/"
    assert spider.scraped_count == 1


def make_header_response(header: str) -> HtmlResponse:
    html = f"""
    <html>
        <body>
            <div class="b-vacancies-head">
                <div class="b-inner-page-header"><h1>{header}</h1></div>
            </div>
        </body>
    </html>
    """
    return HtmlResponse(
        url="https://jobs.dou.ua/vacancies/",
        body=html,
        encoding="utf-8",
        request=scrapy.Request(url="https://jobs.dou.ua/vacancies/"),
    )


@pytest.mark.parametrize(
    "header, expected",
    [
        ("153 jobs  in the Python category", 153),
        ("1\xa0234 вакансії в категорії Python", 1234),
        ("No jobs in the Python category", None),
    ],
)
def test_dou_get_total_jobs(header, expected):
    response = make_header_response(header)
    assert DouUaSpider.get_total_jobs(response) == expected


def test_dou_get_total_jobs_without_header():
    response = HtmlResponse(
        url="https://jobs.dou.ua/vacancies/",
        body="<html><body></body></html>",
        encoding="utf-8",
    )
    assert DouUaSpider.get_total_jobs(response) is None


def test_dou_parse_sets_expected_total_from_first_page():
    spider = DouUaSpider()
    list(spider.parse(make_header_response("153 jobs in Python")))
    assert spider.expected_total == 153


def test_dou_expected_total_is_capped_by_limit():
    spider = DouUaSpider()
    spider.set_expected_total(make_header_response(f"{spider.limit + 1}"))
    assert spider.expected_total == spider.limit


@patch("scraping.job_scraping.spiders.douua.logger")
def test_dou_log_progress_every_n_jobs(mock_logger):
    spider = DouUaSpider()
    spider.expected_total = 153

    spider.scraped_count = PROGRESS_LOG_EVERY - 1
    spider.log_progress()
    mock_logger.info.assert_not_called()

    spider.scraped_count = PROGRESS_LOG_EVERY
    spider.log_progress()
    message = mock_logger.info.call_args.args[0]
    assert f"Scraped {PROGRESS_LOG_EVERY}/153 jobs" in message


@patch("scraping.job_scraping.spiders.douua.logger")
def test_dou_log_progress_falls_back_to_found_jobs(mock_logger):
    spider = DouUaSpider()
    spider.seen_urls = {f"https://jobs.dou.ua/{i}/" for i in range(60)}

    spider.scraped_count = PROGRESS_LOG_EVERY
    spider.log_progress()
    message = mock_logger.info.call_args.args[0]
    assert f"Scraped {PROGRESS_LOG_EVERY}/60 jobs" in message


@patch("scraping.scraper.CrawlerProcess")
def test_scrape_jobs_success(mock_crawler_process):
    mock_process_instance = MagicMock()
    mock_crawler_process.return_value = mock_process_instance

    scrape_jobs()

    mock_crawler_process.assert_called_once()
    mock_process_instance.crawl.assert_called_once()
    mock_process_instance.start.assert_called_once()


@patch("scraping.scraper.CrawlerProcess")
def test_scrape_jobs_failure(mock_crawler_process):
    mock_process_instance = MagicMock()
    mock_process_instance.start.side_effect = Exception("Request failed")
    mock_crawler_process.return_value = mock_process_instance

    with pytest.raises(SystemExit) as exc_info:
        scrape_jobs()

    assert exc_info.value.code == 1
    mock_process_instance.start.assert_called_once()
