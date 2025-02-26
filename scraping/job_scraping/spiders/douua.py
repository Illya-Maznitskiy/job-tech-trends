import scrapy

from config import DOUUA_URL


class DouuaSpider(scrapy.Spider):
    name = "douua"
    allowed_domains = ["dou.ua"]
    start_urls = [DOUUA_URL]

    def parse(self, response):
        for job in response.css("li.l-vacancy"):
            title = job.css("a.vt::text").get()
            job_url = job.css("a.vt::attr(href)").get()

            yield response.follow(
                job_url, callback=self.parse_job_details, meta={"title": title}
            )

    def parse_job_details(self, response):
        title = response.meta.get("title", "No title")

        description = response.css("div.b-typo.vacancy-section p::text").get()
        location = response.css("span.place.bi.bi-geo-alt-fill::text").get()
        date_posted = response.css("div.date::text").get()

        yield {
            "title": title,
            "description": description,
            "location": location,
            "date_posted": date_posted,
            "url": response.url,
        }


# TODO: Check the correctness of all data & Add pagination logic
