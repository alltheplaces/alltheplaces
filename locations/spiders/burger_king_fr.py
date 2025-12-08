import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingFRSpider(scrapy.Spider):
    name = "burger_king_fr"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://ecoceabkstorageprdnorth.blob.core.windows.net/static/restaurants.json"]

    def parse(self, response):
        for location in response.json()["restaurants"].values():
            yield self.parse_store(location)

    def parse_store(self, location: dict) -> Feature:
        item = DictParser.parse(location)
        item["branch"] = item.pop("name", "").upper().removeprefix("BURGER KING ").title()
        item["website"] = location["canonicalURL"]

        if rules := location["openings"].get("room"):
            item["opening_hours"] = self.parse_opening_hours(rules)

        if rules := location["openings"].get("drive"):
            item["extras"]["opening_hours:drive_through"] = self.parse_opening_hours(rules).as_opening_hours()

        apply_yes_no(Extras.AIR_CONDITIONING, item, "AIR_COND" in location["services"])
        apply_yes_no(Extras.OUTDOOR_SEATING, item, "TERRACE" in location["services"])
        apply_yes_no(Extras.TAKEAWAY, item, "TAKEAWAY" in location["services"])
        apply_yes_no(Extras.DELIVERY, item, "DELIVERY" in location["services"])
        apply_yes_no(Extras.DRIVE_THROUGH, item, "DRIVE" in location["services"])
        apply_yes_no(Extras.WIFI, item, "FREE_WIFI" in location["services"])

        return item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, times in rules.items():
            oh.add_range(day, times["opening"], times["closing"])
        return oh
