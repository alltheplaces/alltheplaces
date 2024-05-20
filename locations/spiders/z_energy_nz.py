import json

import scrapy

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class ZEnergyNZSpider(scrapy.Spider):
    name = "z_energy_nz"
    item_attributes = {"brand": "Z", "brand_wikidata": "Q8063337"}
    start_urls = ["https://www.z.co.nz/find-a-station/"]

    def parse(self, response, **kwargs):
        for location in json.loads(
            response.xpath('//script[contains(text(), "stations")]/text()').re_first(r"({\"stations\":.+});")
        )["stations"]:
            item = DictParser.parse(location)
            item["ref"] = location["externalID"]
            item["website"] = f'https://www.z.co.nz{location["link"]}'

            if location["type_slug"] == "airstop":
                apply_category({"aeroway": "fuel"}, item)
            elif location["type_slug"] == "service-station":
                apply_category(Categories.FUEL_STATION, item)
            elif location["type_slug"] == "truck-stop":
                apply_category(Categories.FUEL_STATION.value | {"hgv": "only"}, item)

            apply_yes_no(Fuel.DIESEL, item, any("Diesel" in s["name"] for s in location["fuels"]))

            if postcode := item.get("postcode"):
                item["postcode"] = str(postcode)

            yield item
