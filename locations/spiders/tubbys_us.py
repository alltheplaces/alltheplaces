import json
import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class TubbysUSSpider(scrapy.Spider):
    name = "tubbys_us"
    item_attributes = {"brand": "Tubby's", "brand_wikidata": "Q7850742"}
    allowed_domains = ["tubbys.com"]
    start_urls = ["https://www.tubbys.com/wp-json/wp/v2/location?per_page=100"]
    # robots.txt disallows all query string URLs, which blocks the REST API request above
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        # The "location" custom post type does not expose its ACF fields (address,
        # phone, coordinates, hours) via the REST API, so each location page has to
        # be crawled individually for that data.
        for location in response.json():
            yield scrapy.Request(location["link"], meta={"location_id": location["id"]}, callback=self.parse_location)

    def parse_location(self, response):
        item = Feature()
        item["ref"] = str(response.meta["location_id"])
        item["website"] = response.url
        item["branch"] = re.sub(r"^Tubby.s\s*[‐-―-]\s*", "", response.css("h1::text").get("").strip())
        item["phone"] = response.css('a[href^="tel:"]::text').get()

        if addr_full := response.css(".brxe-shortcode.md-line-height-m::text").get():
            addr_full = " ".join(addr_full.split())
            item["addr_full"] = addr_full
            # look for the postcode after the state, since the house number can
            # itself coincidentally be a 5-digit number
            if m := re.search(r"\b(?:MI|Michigan)\b\D*(\d{5})\b", addr_full):
                item["postcode"] = m.group(1)
            if re.search(r"\bMichigan\b|\bMI\b", addr_full):
                item["state"] = "MI"

        if map_options := response.css(".md-location-map::attr(data-bricks-map-options)").get():
            if addresses := json.loads(map_options).get("addresses"):
                item["lat"] = addresses[0].get("latitude")
                item["lon"] = addresses[0].get("longitude")

        oh = OpeningHours()
        hours_texts = [
            block.css("div.brxe-text-basic::text").getall()[-1] for block in response.css(".md-block-hours__item")
        ]
        for day, hours_text in zip(DAYS, hours_texts):
            hours_text = hours_text.strip()
            if hours_text.upper() == "CLOSED":
                oh.add_range(day, "closed", "closed")
                continue
            if m := re.match(r"(\d{1,2}(?::\d{2})?)\s*(AM|PM)\s*-\s*(\d{1,2}(?::\d{2})?)\s*(AM|PM)", hours_text, re.I):
                open_time, close_time = m.group(1, 3)
                if ":" not in open_time:
                    open_time += ":00"
                if ":" not in close_time:
                    close_time += ":00"
                oh.add_range(
                    day, open_time + m.group(2).upper(), close_time + m.group(4).upper(), time_format="%I:%M%p"
                )
        item["opening_hours"] = oh

        apply_category(Categories.FAST_FOOD, item)
        yield item
