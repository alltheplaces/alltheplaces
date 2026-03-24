from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours, day_range


class ColesAUSpider(Spider):
    name = "coles_au"

    BRANDS = {
        2: {"brand": "Coles", "brand_wikidata": "Q1108172"},
        3: {"brand": "Liquorland", "brand_wikidata": "Q2283837"},
        4: {"brand": "First Choice Liquor", "brand_wikidata": "Q4596269"},
        5: {"brand": "Vintage Cellars", "brand_wikidata": "Q7932815"},
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in point_locations("au_centroids_20km_radius.csv"):
            yield JsonRequest(
                f"https://apigw.coles.com.au/digital/colesweb/v1/stores/search?latitude={lat}&longitude={lon}&brandIds=1,2,3,4,5&numberOfStores=15",
            )

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            location["street_address"] = location.pop("address")
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")

            if brand := self.BRANDS.get(location["brandId"]):
                item.update(brand)
            elif location["brandId"] == 1:
                continue
            else:
                self.logger.error("Unknown brand: {}".format(location["brandName"]))

            if location["brandId"] == 1:
                apply_category(Categories.SHOP_CONVENIENCE, item)

            try:
                item["opening_hours"] = self.parse_opening_hours(location["tradingHours"])
            except:
                self.logger.error("Unable to parse opening hours: {}".format(location["tradingHours"]))

            yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if "-" in rule["daysOfWeek"]:
                days = day_range(*rule["daysOfWeek"].split("-"))
            else:
                days = [rule["daysOfWeek"]]

            if rule["storeTime"] == "24 hours":
                oh.add_days_range(days, "00:00", "24:00")
            elif rule["storeTime"] == "Closed":
                oh.set_closed(days)
            else:
                start_time, end_time = rule["storeTime"].split("-")
                if ":" not in start_time:
                    start_time = start_time.replace("am", ":00am").replace("pm", ":00pm")
                if ":" not in end_time:
                    end_time = end_time.replace("am", ":00am").replace("pm", ":00pm")
                oh.add_days_range(days, start_time, end_time, "%I:%M%p")

        return oh
