from datetime import datetime
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours

BRANDS = {
    "Murphy Express": {"name": "Murphy Express", "brand": "Murphy Express", "brand_wikidata": "Q19604459"},
    "Murphy USA": {"name": "Murphy USA", "brand": "Murphy USA", "brand_wikidata": "Q19604459"},
}


class MurphyUsaUSSpider(Spider):
    name = "murphy_usa_us"
    allowed_domains = ["service.murphydriverewards.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest("https://service.murphydriverewards.com/api/store/list", callback=self.parse_location_list)

    def parse_location_list(self, response):
        for location in response.json()["data"]:
            store_id = location["id"]
            yield JsonRequest(f"https://service.murphydriverewards.com/api/store/detail/{store_id}")

    def parse(self, response):
        if "data" not in response.json():
            return
        location = response.json()["data"]
        item = DictParser.parse(location)
        item["ref"] = location["storeNumber"]
        item["street_address"] = item.pop("addr_full")

        if brand := BRANDS.get(location["chainName"]):
            item.update(brand)
        else:
            self.logger.error("Unexpected brand: {}".format(location["chainName"]))

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            day_name = day.lower()
            if location.get(f"{day_name}Open") and location.get(f"{day_name}Close"):
                item["opening_hours"].add_range(
                    day, location.get(f"{day_name}Open"), location.get(f"{day_name}Close"), "%I:%M%p"
                )

        if start_date := location["openDate"]:
            item["extras"]["start_date"] = datetime.strptime(start_date, "%m/%d/%Y").strftime("%Y-%m-%d")

        apply_yes_no(Extras.TOILETS, item, location.get("hasPublicRestroom"), "hasPublicRestroom" in location)
        apply_yes_no(Fuel.DIESEL, item, location.get("sellDiesel"), "sellDiesel" in location)
        apply_yes_no(Extras.ATM, item, location.get("hasAtm"), "hasAtm" in location)
        apply_yes_no(Extras.CAR_WASH, item, location.get("hasCarWash"), "hasCarWash" in location)
        apply_yes_no(Fuel.PROPANE, item, location.get("sellsPropane"), "sellsPropane" in location)

        fuel_types = [gas_price["fuelType"] for gas_price in location["gasPrices"]]
        apply_yes_no(Fuel.OCTANE_87, item, "Regular" in fuel_types)
        apply_yes_no(Fuel.OCTANE_89, item, "Midgrade" in fuel_types)
        apply_yes_no(Fuel.OCTANE_91, item, "Premium" in fuel_types)

        apply_category(Categories.FUEL_STATION, item)

        yield item
