from scrapy import Spider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class RompetrolSpider(Spider):
    name = "rompetrol"
    item_attributes = {"brand": "Rompetrol", "brand_wikidata": "Q1788862"}
    allowed_domains = [
        "www.rompetrol.bg",
        "www.rompetrol.ge",
        "www.rompetrol.md",
        "www.rompetrol.ro",
    ]
    start_urls = [
        "https://www.rompetrol.bg/routeplanner/stations?language_id=1",
        "https://www.rompetrol.ge/routeplanner/stations?language_id=1",
        "https://www.rompetrol.md/routeplanner/stations?language_id=1",
        "https://www.rompetrol.ro/routeplanner/stations?language_id=1",
    ]

    def parse(self, response):
        for location in response.json():
            location["street_address"] = location.pop("address", None)
            item = DictParser.parse(location)

            if "www.rompetrol.bg" in response.url:
                item["country"] = "BG"
            elif "www.rompetrol.ge" in response.url:
                item["country"] = "GE"
            elif "www.rompetrol.md" in response.url:
                item["country"] = "MD"
            elif "www.rompetrol.ro" in response.url:
                item["country"] = "RO"

            apply_yes_no(Fuel.OCTANE_98, item, "27" in location["services"], False)
            apply_yes_no(Fuel.OCTANE_95, item, "28" in location["services"], False)
            apply_yes_no(Fuel.GTL_DIESEL, item, "30" in location["services"], False)
            apply_yes_no(Fuel.DIESEL, item, "31" in location["services"], False)
            apply_yes_no(Fuel.ADBLUE, item, "14" in location["services"], False)
            apply_yes_no(Fuel.LPG, item, "5" in location["services"], False)
            apply_yes_no(Extras.VACUUM_CLEANER, item, "21" in location["services"], False)
            apply_yes_no(Extras.SHOWERS, item, "15" in location["services"], False)
            apply_yes_no(Extras.WIFI, item, "7" in location["services"], False)

            apply_category(Categories.FUEL_STATION, item)
            if "14" in location["services"]:
                apply_category(Categories.CHARGING_STATION, item)
            if "33" in location["services"]:
                apply_category(Categories.SHOP_LAUNDRY, item)
            if "20" in location["services"]:
                apply_category(Categories.COMPRESSED_AIR, item)
            if "17" in location["services"]:
                apply_category(Categories.RESTAURANT, item)

            yield item
