import json
import re
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, Extras, Fuel, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class Dats24BESpider(Spider):
    name = "dats_24_be"
    item_attributes = {"brand": "DATS 24", "brand_wikidata": "Q15725576", "extras": Categories.FUEL_STATION.value}
    start_urls = ["https://dats24.be/api/service_point_locator"]
    allowed_domains = ["dats24.be"]

    async def start(self) -> AsyncIterator[Request]:
        query = '{"latitude":50.7360328,"longitude":2.4155658,"searchRadius":230447,"serviceDeliveryPointType":["FUEL"],"fuelProductType":[]}'
        yield Request(
            url=self.start_urls[0],
            method="POST",
            body=query,
            headers={"Content-Type": "text/plain;charset=UTF-8"},
            callback=self.parse_locations_list,
        )

    def parse_locations_list(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["addressNumber"], item["street_address"]])
            yield Request(
                url=f"https://dats24.be/nl/particulier/sdp/tankstation-{item.get('branch').replace(' (','-').replace(')','_')}_{location['id']}",
                meta={"item": item},
                callback=self.parse_fuel_details,
            )

    def parse_fuel_details(self, response):
        item = response.meta["item"]
        item["website"] = response.url
        fuel_details = json.loads(re.search(r"FuelProduct\"\s*:\s*(\[.+\]),\"FuelPump", response.text).group(1))
        product_codes = [product["code"] for product in fuel_details]
        apply_yes_no(Fuel.E10, item, "U" in product_codes, False)
        apply_yes_no(Fuel.OCTANE_98, item, "P" in product_codes, False)
        apply_yes_no(Fuel.DIESEL, item, "D" in product_codes, False)
        apply_yes_no(Fuel.CNG, item, "C" in product_codes, False)
        apply_yes_no(Fuel.ADBLUE, item, "A" in product_codes, False)
        apply_yes_no(Extras.COMPRESSED_AIR, item, "B" in product_codes, False)
        yield item
