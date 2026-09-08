import json

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
                yield scrapy.FormRequest(
                    url="https://jobs.dou.ua/vacancies/xhr-load/",
                    formdata={
                        "csrfmiddlewaretoken": csrf_token,
                        "count": str(len(self.seen_urls)),
                    },
                    headers={
                        "X-Requested-With": "XMLHttpRequest",
                        "Referer": response.url,
                    },
                    meta={"csrf_token": csrf_token},
                    callback=self.parse,
                )

        except Exception as e:
            logger.error(f"Error extracting job: {e}")

        logger.info(f"Total DOU jobs scraped: {len(self.seen_urls)}")

    @staticmethod
    def parse_job_details(response):
        title = response.meta.get("title", "No title")
        company_name = response.meta.get("company_name", "No company")

        description = response.css(
            "div.b-typo.vacancy-section p::text"
        ).getall()
        ul_items = response.css(
            "div.b-typo.vacancy-section ul li::text"
        ).getall()

        full_description = description + ul_items
        location = response.css("span.place.bi.bi-geo-alt-fill::text").get()
        date_posted = response.css("div.date::text").get()

        yield {
            RawJobColumns.TITLE: title,
            RawJobColumns.COMPANY_NAME: company_name,
            RawJobColumns.DESCRIPTION: full_description,
            RawJobColumns.LOCATION: location,
            RawJobColumns.DATE_POSTED: date_posted,
            RawJobColumns.URL: response.url,
        }
