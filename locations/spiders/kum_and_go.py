import scrapy

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

FUEL_TYPES_MAPPING = {
    "CNG": Fuel.CNG,
    "Diesel": Fuel.DIESEL,
    "Dyed Diesel": Fuel.UNTAXED_DIESEL,
    "E85": Fuel.E85,
    "E15": Fuel.E15,
    "Kerosene": Fuel.KEROSENE,
    "Midgrade - Ethanol Free": Fuel.ETHANOL_FREE,
    "Midgrade": Fuel.OCTANE_87,
    "Premium - Ethanol Free": Fuel.ETHANOL_FREE,
    "Premium Plus (93 octane)": Fuel.OCTANE_93,
    "Premium": Fuel.OCTANE_91,
    "Super Unleaded/Regular": Fuel.OCTANE_87,
    "Xtreme Diesel": Fuel.DIESEL,
}


class KumAndGoSpider(scrapy.Spider):
    name = "kum_and_go"
    item_attributes = {"brand": "Kum & Go", "brand_wikidata": "Q6443340"}
    allowed_domains = ["kumandgo.com"]
    skip_auto_cc_spider_name = True

    def start_requests(self):
        states = [
            "ar",
            "co",
            "ia",
            "mn",
            "mo",
            "mt",
            "ne",
            "nd",
            "ok",
            "sd",
            "wy",
        ]
        for state in states:
            yield scrapy.Request(f"https://app.kumandgo.com/api/stores/nearest?q={state}")

    def parse(self, response):
        for store in response.json().get("data"):
            item = DictParser.parse(store)
            fuels = store["features"].get("fuelProducts")
            if fuels:
                apply_category(Categories.FUEL_STATION, item)
                for fuel in fuels:
                    if tag := FUEL_TYPES_MAPPING.get(fuel):
                        apply_yes_no(tag, item, True)
                    else:
                        self.crawler.stats.inc_value(f"kum_and_go/fuel_not_mapped/{fuel}")
            else:
                apply_category(Categories.SHOP_CONVENIENCE, item)

            oh = OpeningHours()
            for hours in store["storeHours"].get("hours"):
                if hours.get("displayText") is not None:
                    oh.add_ranges_from_string(hours.get("day") + " " + hours.get("displayText"))
            item["opening_hours"] = oh
            item["website"] = "https://www.kumandgo.com/store-locator?details={}".format(item["ref"])

            yield item
