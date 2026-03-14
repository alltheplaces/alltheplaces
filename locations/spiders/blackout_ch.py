from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class BlackoutCHSpider(Spider):
    name = "blackout_ch"
    item_attributes = {"brand": "Blackout", "brand_wikidata": "Q118074688"}
    start_urls = ["https://www.blackout.ch/storefinder"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "window.storeLocations =")]').get()
        ).values():
            if location["name_2"] != "BLACKOUT":
                raise Exception(location)
            item = Feature()
            item["ref"] = location["code"]
            item["branch"] = location["name"]
            item["street_address"] = location["address"]
            item["postcode"] = location["post_code"]
            item["city"] = location["city"]
            item["phone"] = location["phone_no"]
            item["lat"] = location["coordinates_latitude"]
            item["lon"] = location["coordinates_longitude"]
            item["extras"]["ref:google:place_id"] = location["google_place_id"]

            item["opening_hours"] = self.parse_opening_hours(location)

            apply_category(Categories.SHOP_CLOTHES, item)

            yield item

    def parse_opening_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            if location.get("break_from_{}".format(day)) and location["break_from_{}".format(day)] != "00:00:00":
                oh.add_range(
                    day, location["open_from_{}".format(day)], location["break_from_{}".format(day)], "%H:%M:%S"
                )
                oh.add_range(
                    day, location["break_till_{}".format(day)], location["open_till_{}".format(day)], "%H:%M:%S"
                )
            elif location.get("open_from_{}".format(day)):
                oh.add_range(
                    day, location["open_from_{}".format(day)], location["open_till_{}".format(day)], "%H:%M:%S"
                )

        return oh
