import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class GiordanosUSSpider(scrapy.Spider):
    name = "giordanos_us"
    item_attributes = {"brand": "Giordano's Pizzeria", "brand_wikidata": "Q5563393"}
    start_urls = ["https://giordanos.com/all-locations/"]
    # The site rejects requests with HTTP 400 when too many concurrent
    # connections are open, so restrict this spider to one at a time.
    custom_settings = {"CONCURRENT_REQUESTS_PER_DOMAIN": 1}

    def parse(self, response):
        for url in response.css("#locations-list a::attr(href)").getall():
            if "/locations/search" in url:
                continue
            yield response.follow(url, callback=self.parse_item)

    def parse_item(self, response):
        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        item["branch"] = response.css("h1::text").get("").strip()

        addr_lines = response.css(".address a::text").getall()
        item["street_address"] = addr_lines[0].strip()
        city_state_zip = re.sub(r"\s+", " ", addr_lines[1]).strip()
        city, _, rest = city_state_zip.partition(",")
        state, _, postcode = rest.strip().rpartition(" ")
        item["city"] = city.strip()
        item["state"] = state.strip()
        item["postcode"] = postcode.strip()

        if daddr := response.css(".address a::attr(href)").get():
            if m := re.search(r"daddr=(-?\d+\.\d+),(-?\d+\.\d+)", daddr):
                item["lat"], item["lon"] = m.groups()

        if tel := response.css(".phone a::attr(href)").get():
            item["phone"] = tel.removeprefix("tel:")

        oh = OpeningHours()
        oh.add_ranges_from_string("; ".join(response.css(".hours::text").getall()))
        item["opening_hours"] = oh

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"

        yield item
