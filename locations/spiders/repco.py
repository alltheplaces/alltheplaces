from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class RepcoSpider(Spider):
    name = "repco"
    item_attributes = {"brand": "Repco", "brand_wikidata": "Q173425"}
    allowed_domains = [
        "www.repco.com.au",
        "www.repco.co.nz",
    ]
    start_urls = [
        "https://www.repco.com.au/en/store-finder/store-locator?q=&page=0",
        "https://www.repco.co.nz/en/store-finder/store-locator?q=&page=0",
    ]
    requires_proxy = "AU"  # or NZ

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.crawl_pages)

    def crawl_pages(self, response):
        page_count = response.json()["numberOfPages"]
        for page_number in range(1, page_count - 1, 1):
            yield JsonRequest(response.url.replace("&page=0", f"&page={page_number}"))
        self.parse(response)

    def parse(self, response):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["ref"] = location["name"].strip()
            item["name"] = location["displayName"].strip()
            item["street_address"] = location["line1"].strip()
            if location["line2"].strip():
                item["street_address"] = item["street_address"] + ", " + location["line2"].strip()
            item["street_address"] = item["street_address"].replace("&amp;", "&")
            slug = "Repco_" + location["url"].strip().replace("/store/", "").title().replace(" ", "-")
            if "repco.com.au" in response.url:
                item["website"] = f"https://www.repco.com.au/en/store/{slug}"
            elif "repco.co.nz" in response.url:
                item["website"] = f"https://www.repco.co.nz/en/store/{slug}"

            item["opening_hours"] = OpeningHours()
            for day_name, hours in location["openings"].items():
                if hours.upper() == "CLOSED":
                    continue
                item["opening_hours"].add_range(
                    DAYS_EN[day_name], hours.split(" - ")[0], hours.split(" - ")[1], "%I:%M %p"
                )

            yield item
