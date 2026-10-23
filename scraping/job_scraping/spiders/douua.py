import json
import re
from typing import Sequence
from urllib.parse import urlparse, parse_qs
import time

import scrapy
from scrapy import Selector
from scrapy.http import Response

from config import (
    DOU_UA_URL,
    RawJobColumns,
    MAX_ITEMS_TO_SCRAPE,
    Scraper,
    PROGRESS_LOG_EVERY,
)
from logger import logger


class DouUaSpider(scrapy.Spider):
    name = "dou_ua"
    allowed_domains = ["dou.ua", "jobs.dou.ua"]
    start_urls = [DOU_UA_URL]
    limit = MAX_ITEMS_TO_SCRAPE[Scraper.DOU_UA]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_urls = set()
        self.scraped_count = 0
        self.expected_total = None
        self.start_time = time.time()
        parsed_url = urlparse(DOU_UA_URL)
        query_params = parse_qs(parsed_url.query)
        self.category = query_params.get("category", [None])[0]

    @staticmethod
    def get_jobs_data(response: Response) -> Sequence[Selector]:
        try:
            data = json.loads(response.text)
            html = data.get("html", "")

            sel = Selector(text=html)
            return sel.css("li.l-vacancy")
        except json.JSONDecodeError:
            return response.css("li.l-vacancy")

    @staticmethod
    def clean_text(text: str | None) -> str:
        if not text:
            return ""
        # Normalize NBSP symbols, spaces
        return re.sub(r"[\s\xa0]+", " ", text).strip()

    @staticmethod
    def get_total_jobs(response: Response) -> int | None:
        # Header example: "153 jobs  in the Python category"
        header = response.css("div.b-vacancies-head h1::text").get()
        match = re.search(r"\d[\d\s\xa0]*", header or "")
        if not match:
            return None
        # Remove spaces inside big numbers: "1 234" -> 1234
        return int(re.sub(r"\D", "", match.group()))

    def set_expected_total(self, response: Response) -> None:
        total = self.get_total_jobs(response)
        if total is None:
            logger.warning(
                "Total DOU jobs not found, ETA uses jobs found so far"
            )
            return
        self.expected_total = min(total, self.limit)
        logger.info(f"Expected DOU jobs: ~{self.expected_total}")

    def log_progress(self) -> None:
        if self.scraped_count % PROGRESS_LOG_EVERY != 0:
            return
        # Best guess of all jobs to scrape: header count or jobs found so far
        estimated_total = self.expected_total or len(self.seen_urls)
        avg_per_job = (time.time() - self.start_time) / self.scraped_count
        jobs_left = max(estimated_total - self.scraped_count, 0)
        time_left = jobs_left * avg_per_job
        logger.info(
            f"Scraped {self.scraped_count}/{estimated_total} jobs, "
            f"{avg_per_job:.2f}s/job, ~{time_left:.0f}s left"
        )

    def parse(self, response):
        try:
            # Only the first page has the header with the total
            if not response.meta.get("csrf_token"):
                self.set_expected_total(response)

            jobs = self.get_jobs_data(response)
            for job in jobs:
                if len(self.seen_urls) >= self.limit:
                    return
                job_url = job.css("a.vt::attr(href)").get()
                title = job.css("a.vt::text").get()
                company_name = job.css("a.company::text").get()

                if job_url in self.seen_urls:
                    continue
                self.seen_urls.add(job_url)

                yield response.follow(
                    job_url,
                    callback=self.parse_job_details,
                    meta={"title": title, "company_name": company_name},
                )

            # simulate clicking button through a request
            csrf_token = response.meta.get("csrf_token")

            # if the first request, get the csrf token from the response
            if not csrf_token:
                payload = response.text
                match = re.search(
                    r'window\.CSRF_TOKEN\s*=\s*["\']([^"\']+)["\'];', payload
                )
                if match:
                    csrf_token = match.group(1)

            if csrf_token and len(self.seen_urls) < self.limit:
                formdata = {
                    "csrfmiddlewaretoken": csrf_token,
                    "count": str(len(self.seen_urls)),
                }

                if self.category:
                    formdata["category"] = self.category

                parsed_base = urlparse(DOU_UA_URL)
                query_string = (
                    f"?{parsed_base.query}" if parsed_base.query else ""
                )

                yield scrapy.FormRequest(
                    url=(
                        "https://jobs.dou.ua/vacancies/xhr-load/"
                        f"{query_string}"
                    ),
                    formdata=formdata,
                    headers={
                        "X-Requested-With": "XMLHttpRequest",
                        "Referer": DOU_UA_URL,
                    },
                    meta={"csrf_token": csrf_token},
                    callback=self.parse,
                )

        except Exception as e:
            logger.error(f"Error extracting job: {e}")

    def parse_job_details(self, response):
        title = response.meta.get("title", "No title")
        company_name = response.meta.get("company_name", "No company")

        description = response.css(
            "div.b-typo.vacancy-section p::text"
        ).getall()
        ul_items = response.css(
            "div.b-typo.vacancy-section ul li::text"
        ).getall()

        raw_description = " ".join(description + ul_items)
        location = response.css("span.place.bi.bi-geo-alt-fill::text").get()
        date_posted = response.css("div.date::text").get()

        self.scraped_count += 1
        self.log_progress()

        yield {
            RawJobColumns.TITLE: self.clean_text(title),
            RawJobColumns.COMPANY_NAME: self.clean_text(company_name),
            RawJobColumns.DESCRIPTION: self.clean_text(raw_description),
            RawJobColumns.LOCATION: self.clean_text(location),
            RawJobColumns.DATE_POSTED: self.clean_text(date_posted),
            RawJobColumns.URL: response.url,
        }

    def closed(self, reason):
        logger.info(f"Total DOU jobs scraped: {self.scraped_count}")
        total_time = time.time() - self.start_time
        avg_per_job = (
            total_time / self.scraped_count if self.scraped_count else 0
        )
        logger.info(f"Total Time    : {total_time:.2f}s")
        logger.info(f"Avg/Job Time  : {avg_per_job:.2f}s")
