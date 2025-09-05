from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class OkDKSpider(Spider):
    name = "ok_dk"
    item_attributes = {"brand": "OK", "brand_wikidata": "Q12329785", "country": "DK"}
    start_urls = ["https://www.ok.dk/privat/paa-tanken/find-tank/gettankstationer"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["tankstationer"]:
            item = DictParser.parse(location)
            item["lon"] = location["longtitude"]
            item["branch"] = location["navn"]
            item["addr_full"] = location["adresse"]

            if location["erTank"] is True:
                fuel = item.deepcopy()
                fuel["ref"] = "{}-fuel".format(item["ref"])
                apply_category(Categories.FUEL_STATION, fuel)
                yield fuel

            if location["harButik"] is True:
                shop = item.deepcopy()
                shop["ref"] = "{}-shop".format(item["ref"])
                apply_category(Categories.SHOP_CONVENIENCE, shop)
                yield shop
