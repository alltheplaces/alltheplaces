import re

import chompjs
from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class BrickHouseTavernAndTapUSSpider(Spider):
    name = "brick_house_tavern_and_tap_us"
    item_attributes = {"brand": "Brick House Tavern + Tap", "country": "US"}
    allowed_domains = ["www.brickhousetavernandtap.com"]
    start_urls = ["https://www.brickhousetavernandtap.com/store-locator/"]

    def parse(self, response):
        config = chompjs.parse_js_object(response.text.split("storeLocatorConfig(", 1)[1])

        for location in config["locations"]:
            item = Feature(
                ref=location["slug"],
                name=self.item_attributes["brand"],
                branch=location["name"].rstrip("*"),
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

            item["extras"]["cuisine"] = "american"
            apply_category(Categories.RESTAURANT, item)
            yield item
