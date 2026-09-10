import json
import re
from urllib.parse import urlparse, parse_qs
import time

import scrapy

from config import DOU_UA_URL, RawJobColumns, MAX_ITEMS_TO_SCRAPE, Scraper
from logger import logger


class DouUaSpider(scrapy.Spider):
    name = "dou_ua"
    allowed_domains = ["dou.ua", "jobs.dou.ua"]
    start_urls = [DOU_UA_URL]
    limit = MAX_ITEMS_TO_SCRAPE[Scraper.DOU_UA]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_urls = set()
        self.start_time = time.time()
        parsed_url = urlparse(DOU_UA_URL)
        query_params = parse_qs(parsed_url.query)
        self.category = query_params.get("category", [None])[0]

    @staticmethod
    def get_jobs_data(response) -> dict:
        try:
            data = json.loads(response.text)
            html = data.get("html", "")
            from scrapy import Selector

            sel = Selector(text=html)
            jobs = sel.css("li.l-vacancy")
        except json.JSONDecodeError:
            jobs = response.css("li.l-vacancy")

        return jobs

    @staticmethod
    def clean_text(text: str | None) -> str:
        if not text:
            return ""
        # Normalize NBSP symbols, spaces
        return re.sub(r"[\s\xa0]+", " ", text).strip()

    def parse(self, response):
        try:
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

            if not csrf_token:
                # Only try CSS if it's the first run on HTML page
                try:
                    csrf_token = response.css(
                        "input[name='csrfmiddlewaretoken']::attr(value)"
                    ).get()
                except ValueError:
                    csrf_token = response.cookies.get("csrftoken")

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

        yield {
            RawJobColumns.TITLE: self.clean_text(title),
            RawJobColumns.COMPANY_NAME: self.clean_text(company_name),
            RawJobColumns.DESCRIPTION: self.clean_text(raw_description),
            RawJobColumns.LOCATION: self.clean_text(location),
            RawJobColumns.DATE_POSTED: self.clean_text(date_posted),
            RawJobColumns.URL: response.url,
        }

    def closed(self, reason):
        logger.info(f"Total DOU jobs scraped: {len(self.seen_urls)}")
        total_time = time.time() - self.start_time
        avg_per_job = (
            total_time / len(self.seen_urls) if len(self.seen_urls) else 0
        )
        logger.info(f"Total Time    : {total_time:.2f}s")
        logger.info(f"Avg/Job Time  : {avg_per_job:.2f}s")
