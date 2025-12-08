from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class VirsiLVSpider(Spider):
    name = "virsi_lv"
    item_attributes = {"brand": "Virši", "brand_wikidata": "Q50378789"}
    start_urls = ["https://www.virsi.lv/en/private/gas-stations/data"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stations"]:
            item = DictParser.parse(location)
            item["state"] = None
            item["branch"] = item.pop("name").removeprefix("Virši ")

            services = [s["title"] for s in location["services"]]

            apply_yes_no(Fuel.CNG, item, "CNG" in services)
            apply_yes_no(Fuel.OCTANE_98, item, "98" in services)
            apply_yes_no(Fuel.OCTANE_95, item, "95E" in services)
            apply_yes_no(Fuel.DIESEL, item, "Diesel" in services)
            apply_yes_no(Fuel.ADBLUE, item, "AdBlue" in services)
            apply_yes_no(Extras.CAR_WASH, item, "Car wash" in services)
            apply_yes_no(Extras.TOILETS, item, "WC" in services)
            apply_yes_no(Extras.WIFI, item, "WiFi" in services)
            apply_yes_no(Extras.COMPRESSED_AIR, item, "Air" in services)

            apply_category(Categories.FUEL_STATION, item)

            yield item
