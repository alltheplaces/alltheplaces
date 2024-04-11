from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class CaltexSpider(Spider):
    name = "caltex"
    item_attributes = {"brand": "Caltex", "brand_wikidata": "Q277470"}
    allowed_domains = ["www.caltex.com"]
    start_urls = [
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/au/en/find-us&siteType=b2c",
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/hk/en/find-a-caltex-station&siteType=b2c",
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/my/en/find-us&siteType=b2c",
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/pk/en/find-us/locators&siteType=b2c",
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/ph/en/find-us&siteType=b2c",
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/sg/en/find-a-caltex-station&siteType=b2c",
        "https://www.caltex.com/bin/services/getStations.json?pagePath=/content/caltex/th/th/find-us&siteType=b2c",
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if location["siteType"] != "Station":
                continue

            item = DictParser.parse(location)

            if location.get("fuelsName"):
                apply_yes_no(
                    Fuel.OCTANE_98,
                    item,
                    "PULP 98" in location["fuelsName"]
                    or (
                        "/hk/" in response.url
                        and (
                            "Gold with Techron Gasoline" in location["fuelsName"]
                            or "Platinum with Techron Gasoline" in location["fuelsName"]
                        )
                    )
                    or "Platinum 98 with Techron" in location["fuelsName"],
                    False,
                )
                apply_yes_no(Fuel.OCTANE_97, item, "Premium 97" in location["fuelsName"], False)
                apply_yes_no(
                    Fuel.OCTANE_95,
                    item,
                    "PULP 95" in location["fuelsName"]
                    or "Premium 95" in location["fuelsName"]
                    or ("/ph/" in response.url and "Platinum with Techron" in location["fuelsName"])
                    or "Platinum with Techron Gasoline" in location["fuelsName"]
                    or "Premium 95 with Techron" in location["fuelsName"]
                    or "Techron Gasohol95" in location["fuelsName"]
                    or "Techron Gold95" in location["fuelsName"],
                    False,
                )
                apply_yes_no(Fuel.OCTANE_92, item, "Regular 92 with Techron" in location["fuelsName"], False)
                apply_yes_no(
                    Fuel.OCTANE_91,
                    item,
                    "Unleaded 91" in location["fuelsName"]
                    or "Silver with Techron" in location["fuelsName"]
                    or "Techron Gasohol91" in location["fuelsName"],
                    False,
                )
                apply_yes_no(Fuel.E10, item, "Unleaded E10" in location["fuelsName"], False)
                apply_yes_no(Fuel.E20, item, "Gasohol E20" in location["fuelsName"], False)
                apply_yes_no(
                    Fuel.LPG, item, "LPG" in location["fuelsName"] or "AutoGas" in location["fuelsName"], False
                )
                apply_yes_no(
                    Fuel.DIESEL,
                    item,
                    "Diesel" in location["fuelsName"]
                    or "Premium Diesel" in location["fuelsName"]
                    or "Diesel Euro5 B10" in location["fuelsName"]
                    or "Power Diesel Euro5 B7" in location["fuelsName"]
                    or "Power Diesel with Techron D Euro 5" in location["fuelsName"]
                    or "Diesel with Techron D" in location["fuelsName"]
                    or "Techron D Diesel B7" in location["fuelsName"]
                    or "Techron D Diesel B10" in location["fuelsName"]
                    or "Techron D Diesel B20" in location["fuelsName"]
                    or "Techron D Power Diesel" in location["fuelsName"],
                    False,
                )
                apply_yes_no(
                    Fuel.ENGINE_OIL,
                    item,
                    "Havoline Engine Oil" in location["fuelsName"] or "Delo Diesel Engine Oil" in location["fuelsName"],
                    False,
                )
                apply_yes_no(Fuel.ADBLUE, item, "Bulk AdBlue" in location["fuelsName"], False)
                apply_yes_no(Fuel.KEROSENE, item, "Kerosene" in location["fuelsName"], False)

            apply_category(Categories.FUEL_STATION, item)

            yield item
