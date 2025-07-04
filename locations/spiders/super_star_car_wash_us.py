from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class SuperStarCarWashUSSpider(Spider):
    name = "super_star_car_wash_us"
    item_attributes = {"brand": "Super Star Car Wash", "brand_wikidata": "Q132156104"}
    start_urls = ["https://www.superstarcarwashaz.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "locationList")]/text()').get()
        ).values():
            if location["types"] == "Coming Soon":
                continue

            item = Feature()
            item["ref"] = location["guid"]
            item["lat"] = location["lat"]
            item["lon"] = location["lon"]
            item["branch"] = location["post_title"]
            item["website"] = response.urljoin(location["post_name"])
            item["addr_full"] = location["addr"]

            try:
                if hours := location.get("hours"):
                    item["opening_hours"] = self.parse_opening_hours(hours)
            except:
                self.logger.error("Error parsing opening hours")

            apply_category(Categories.CAR_WASH, item)

            yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            oh.add_range(rule["day"], rule["opening_time"], rule["closing_time"], time_format="%I:%M %p")
        return oh
