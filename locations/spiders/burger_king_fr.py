import scrapy
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingFRSpider(scrapy.Spider):
    name = "burger_king_fr"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://webapi.burgerking.fr/blossom/api/v12/public/store-locator/all"]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"x-application": "WEBSITE"}}
    requires_proxy = True

    def parse(self, response):
        for location in response.json():
            yield JsonRequest(
                url=f'https://webapi.burgerking.fr/blossom/api/v12/public/restaurant{location["pageUrl"]}/page',
                callback=self.parse_store,
            )

    def parse_store(self, response):
        location = response.json()["restaurant"]
        item = DictParser.parse(location)
        item["branch"] = item.pop("name", "").upper().removeprefix("BURGER KING ").title()
        item["website"] = response.json()["metaData"]["canonicalURL"]
        item["image"] = location["image"][0]
        oh = OpeningHours()
        open_hours = location["openHours"]
        for hours in open_hours:
            if hours["room"] is not None:
                start, end = hours["room"].split("-", maxsplit=1)
                oh.add_range(hours["day"], start.strip(), end.strip(), time_format="%H:%M")
        item["opening_hours"] = oh
        apply_yes_no(Extras.AIR_CONDITIONING, item, "AIR_COND" in location["services"])
        apply_yes_no(Extras.OUTDOOR_SEATING, item, "TERRACE" in location["services"])
        apply_yes_no(Extras.TAKEAWAY, item, "TAKEAWAY" in location["services"])
        apply_yes_no(Extras.DELIVERY, item, "DELIVERY" in location["services"])
        apply_yes_no(Extras.DRIVE_THROUGH, item, "DRIVE" in location["services"])
        apply_yes_no(Extras.WIFI, item, "FREE_WIFI" in location["services"])

        yield item
