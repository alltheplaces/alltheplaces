from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class ApplegreenSpider(Spider):
    name = "applegreen"
    item_attributes = {"brand": "Applegreen", "brand_wikidata": "Q7178908"}
    start_urls = ["https://api.applegreenstores.com/v1/locations?limit=1200&radius=600000"]

    def parse(self, response, **kwargs):
        for location in response.json()["items"]:
            if location["competitor"]:
                continue
            yield JsonRequest(
                url=f'https://api.applegreenstores.com/v1/locations/{location["id"]}', callback=self.parse_location
            )

    def parse_location(self, response, **kwargs):
        location = response.json()["item"]
        item = DictParser.parse(location)
        item["lat"] = location["geolat"]
        item["lon"] = location["geolng"]

        apply_category(Categories.FUEL_STATION, item)

        apply_yes_no(Extras.ATM, item, location["services"]["has_atm"])
        apply_yes_no("sells:lottery", item, location["services"]["has_lotto"])
        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, location["services"]["has_baby_changing"])
        apply_yes_no(Extras.WIFI, item, location["services"]["has_wifi"])

        # Also includes fuel prices

        yield item
