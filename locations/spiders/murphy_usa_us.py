from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class MurphyUsaUSSpider(Spider):
    name = "murphy_usa_us"
    item_attributes = {"brand": "Murphy USA", "brand_wikidata": "Q19604459"}
    allowed_domains = ["service.murphydriverewards.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest("https://service.murphydriverewards.com/api/store/list", callback=self.parse_location_list)

    def parse_location_list(self, response):
        for location in response.json()["data"]:
            store_id = location["id"]
            yield JsonRequest(f"https://service.murphydriverewards.com/api/store/detail/{store_id}")

    def parse(self, response):
        location = response.json()["data"]
        item = DictParser.parse(location)
        item["ref"] = location["storeNumber"]
        item["street_address"] = item.pop("addr_full")
        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            day_name = day.lower()
            if location.get(f"{day_name}Open") and location.get(f"{day_name}Close"):
                item["opening_hours"].add_range(
                    day, location.get(f"{day_name}Open"), location.get(f"{day_name}Close"), "%I:%M%p"
                )
        apply_yes_no(Extras.TOILETS, item, location.get("hasPublicRestroom"), False)
        apply_yes_no(Fuel.DIESEL, item, location.get("sellDiesel"), False)
        apply_yes_no(Extras.ATM, item, location.get("hasAtm"), False)
        apply_yes_no(Extras.CAR_WASH, item, location.get("hasCarWash"), False)
        apply_yes_no(Fuel.PROPANE, item, location.get("sellsPropane"), False)
        fuel_types = [gas_price["fuelType"] for gas_price in location["gasPrices"]]
        apply_yes_no(Fuel.OCTANE_87, item, "Regular" in fuel_types, False)
        apply_yes_no(Fuel.OCTANE_89, item, "Midgrade" in fuel_types, False)
        apply_yes_no(Fuel.OCTANE_91, item, "Premium" in fuel_types, False)
        apply_category(Categories.FUEL_STATION, item)
        yield item
