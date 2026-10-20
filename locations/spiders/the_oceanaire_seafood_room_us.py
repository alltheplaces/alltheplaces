import re

import chompjs
from pycountry import subdivisions
from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

US_STATES = {subdivision.code.removeprefix("US-") for subdivision in subdivisions.get(country_code="US")}


class TheOceanaireSeafoodRoomUSSpider(Spider):
    name = "the_oceanaire_seafood_room_us"
    item_attributes = {"brand": "The Oceanaire Seafood Room", "country": "US"}
    allowed_domains = ["www.theoceanaire.com"]
    start_urls = ["https://www.theoceanaire.com/hours-and-locations/"]

    def parse(self, response):
        config = chompjs.parse_js_object(response.text.split("storeLocatorConfig(", 1)[1])

        for location in config["locations"]:
            if location["state"] not in US_STATES or not re.fullmatch(
                r"\d{5}(?:-\d{4})?", location.get("postal_code") or ""
            ):
                continue

            item = Feature(
                ref=location["slug"],
                name=self.item_attributes["brand"],
                branch=location["name"],
                lat=location["lat"],
                lon=location["lng"],
                street_address=location["street"],
                city=location["city"],
                state=location["state"],
                postcode=location["postal_code"],
                phone=location["phone_number"],
                website=response.urljoin(location["url"]),
            )

            hours = OpeningHours()
            for line in Selector(text=location.get("hours") or "").xpath("//p/text()").getall():
                if re.match(r"\s*(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\s*[-:]", line, re.I):
                    hours.add_ranges_from_string(line)
            if hours.as_opening_hours():
                item["opening_hours"] = hours

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "seafood"
            yield item
