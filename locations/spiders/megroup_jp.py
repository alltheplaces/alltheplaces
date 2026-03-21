from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations, country_iseadgg_centroids

RADIUS_KM = 24


class MegroupJPSpider(Spider):
    name = "megroup_jp"
    item_attributes = {"operator": "ME Group Japan", "operator_wikidata": "Q124004072"}

    def make_request(self, lat, lon):
        return JsonRequest(f"https://locator.me-group.jp/api/Machines/GetNearbyMachines?lat={lat}&lon={lon}")

    async def start(self):
        for lat, lon in country_iseadgg_centroids("JP", RADIUS_KM):
            yield self.make_request(lat, lon)
        for city in city_locations("JP"):
            yield self.make_request(city["latitude"], city["longitude"])

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for loc in response.json():
            item = DictParser.parse(loc)
            item["ref"] = loc["LocNmKanji"]
            item["street_address"] = loc["Address"]
            if loc["MachineType"] == "S":
                item["name"] = "Photo-Me"
                item["branch"] = loc["LocNmKanji"]
                apply_category(Categories.PHOTO_BOOTH, item)
            else:
                apply_category(Categories.VENDING_MACHINE, item)
                if loc["MachineType"] == "O":
                    item["name"] = "Feed ME Orange"
                    item["extras"]["vending"] = "drinks"
                    item["extras"]["drink:orange_juice"] = "yes"
                elif loc["MachineType"] == "A":
                    item["name"] = "Feed ME Apple"
                    item["extras"]["vending"] = "drinks"
                    item["extras"]["drink:apple_juice"] = "yes"
                elif loc["MachineType"] == "N":
                    item["name"] = "NAMES ステッカー"
                    item["extras"]["vending"] = "stickers"

            yield item
