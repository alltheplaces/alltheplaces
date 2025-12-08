import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


# POIs are available for RU and KZ
class CoffeeLikeSpider(scrapy.Spider):
    name = "coffee_like"
    allowed_domains = ["coffee-like.com"]
    item_attributes = {"brand_wikidata": "Q55662627"}
    start_urls = ["https://coffee-like.com/coffee-bars/all"]

    def parse(self, response):
        for poi in response.json()["features"]:
            item = DictParser.parse(poi["properties"])
            item["ref"] = poi["id"]
            item["lat"] = poi["geometry"]["coordinates"][0]
            item["lon"] = poi["geometry"]["coordinates"][1]
            item["image"] = poi["properties"].get("img")
            try:
                oh = OpeningHours()
                working_time = poi["properties"].get("working_time", [])
                for day in working_time:
                    if day.get("begin") and day.get("end"):
                        oh.add_range(DAYS[day.get("weekday")], day.get("begin"), day.get("end"), "%H:%M:%S")
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Fail to parse hours: {working_time}, {e}")
            apply_category(Categories.CAFE, item)
            yield item
