import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class DibellasSubsUSSpider(scrapy.Spider):
    name = "dibellas_subs_us"
    item_attributes = {"brand": "DiBella's Subs", "brand_wikidata": "Q5269976"}
    start_urls = ["https://dibellas.com/api/v2/locations"]

    def parse(self, response):
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["website"] = f"https://dibellas.com/locations/{location['path']}/"
            item["opening_hours"] = self.parse_hours(location.get("hours", []))

            apply_category(Categories.FAST_FOOD, item)

            yield item

    @staticmethod
    def parse_hours(hours) -> OpeningHours:
        oh = OpeningHours()
        for rule in hours:
            day = DAYS_EN.get(rule.get("day", "").capitalize())
            open_time = rule.get("open")
            close_time = rule.get("close")
            if day and open_time and close_time:
                oh.add_range(day, open_time, close_time)
        return oh
