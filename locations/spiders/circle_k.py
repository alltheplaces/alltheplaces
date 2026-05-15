from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class CircleKSpider(Spider):
    name = "circle_k"
    CIRCLE_K = {"brand": "Circle K", "brand_wikidata": "Q3268010"}

    brands = {
        "CIRCLEK": (CIRCLE_K, Categories.SHOP_CONVENIENCE),
        "COUCHE_TARD": ({"brand": "Couche-Tard", "brand_wikidata": "Q2836957"}, Categories.SHOP_CONVENIENCE),
        "HOLIDAY": ({"brand": "Holiday", "brand_wikidata": "Q5880490"}, Categories.SHOP_CONVENIENCE),
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        for country in ["US", "CA"]:
            yield JsonRequest(
                url=f"https://api.circlek.com/us/ngrp-store-locator/v1/stations?bottomRightLongitude=180.0&bottomRightLatitude=-90.0&topLeftLongitude=-180.0&topLeftLatitude=90.0&maxResults=10000&country={country}&brand=CIRCLEK,COUCHE_TARD,HOLIDAY",
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street")
            item["branch"] = location["businessUnit"]
            item["addr_full"] = merge_address_lines(location["address"].values())
            services = [service["displayName"] for service in location["services"]]
            fuels = [fuels["displayName"] for fuels in location["fuels"]]
            apply_yes_no(Extras.ATM, item, "ATM" in services)
            apply_yes_no(Extras.TOILETS, item, "Public Restrooms" in services)
            apply_yes_no(Extras.CAR_WASH, item, "Car wash" in services)
            apply_yes_no(Fuel.ELECTRIC, item, "EV Charging" in services)
            apply_yes_no(Fuel.DIESEL, item, "Diesel" in fuels)
            apply_yes_no(Fuel.GASOLINE, item, "Gas" in fuels)
            brand, cat = self.brands.get(location["brand"], (None, None))
            if brand:
                item.update(brand)
                apply_category(cat, item)
                item["name"] = brand.get("brand")
            else:
                if "Gas" in fuels or "Diesel" in fuels:
                    apply_category(Categories.FUEL_STATION, item)
                else:
                    apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
