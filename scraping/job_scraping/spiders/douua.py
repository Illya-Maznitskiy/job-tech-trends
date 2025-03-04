import time

import scrapy
from selenium import webdriver
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from webdriver_manager.chrome import ChromeDriverManager

from config import DOUUA_URL


class DouuaSpider(scrapy.Spider):
    name = "douua"
    allowed_domains = ["dou.ua"]
    start_urls = [DOUUA_URL]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        chrome_options = Options()
        chrome_options.add_argument("--headless")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
        )

    def parse(self, response):
        self.driver.get(DOUUA_URL)

        while True:
            jobs = self.driver.find_elements(By.CSS_SELECTOR, ".l-vacancy")
            load_more_btn = WebDriverWait(self.driver, 10).until(
                ec.element_to_be_clickable(
                    (By.XPATH, "//a[contains(text(),'Більше вакансій')]")
                )
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", load_more_btn
            )
            time.sleep(1)
            load_more_btn.click()

            for job in jobs:
                try:
                    title = job.find_element(By.CSS_SELECTOR, "a.vt").text
                    company_name = job.find_element(
                        By.CSS_SELECTOR, "a.company"
                    ).text
                    job_url = job.find_element(
                        By.CSS_SELECTOR, "a.vt"
                    ).get_attribute("href")

                    yield response.follow(
                        job_url,
                        callback=self.parse_job_details,
                        meta={"title": title, "company_name": company_name},
                    )
                except NoSuchElementException as e:
                    print(f"Element not found: {e}")
                except TimeoutException as e:
                    print(f"Timeout error: {e}")
                except Exception as e:
                    print(f"Error extracting job: {e}")

    def parse_job_details(self, response):
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
            "title": title,
            "company_name": company_name,
            "description": full_description,
            "location": location,
            "date_posted": date_posted,
            "url": response.url,
        }
