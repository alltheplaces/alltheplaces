from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.central_england_cooperative import set_operator

EG = {"brand": "EG Australia", "brand_wikidata": "Q5023980"}


class AmpolAUSpider(Spider):
    name = "ampol_au"
    item_attributes = {"brand": "Ampol", "brand_wikidata": "Q4748528"}
    allowed_domains = ["www.ampol.com.au"]
    start_urls = ["https://www.ampol.com.au/custom/api/locator/get"]

    def start_requests(self):
        yield JsonRequest(
            url="https://www.ampol.com.au/custom/api/authorize/token",
            method="POST",
            headers={"X-Requested-With": "XMLHttpRequest"},
            callback=self.parse_auth_token,
        )

    def parse_auth_token(self, response):
        token = response.json()
        for url in self.start_urls:
            yield JsonRequest(url=url, headers={"Authorization": f"Bearer {token}"})

    def parse(self, response):
        for location in response.json()["value"]:
            address = location.pop("Address")
            item = DictParser.parse(location)
            item["geometry"] = location["Location"]
            item["street_address"] = address

            if location["Brand"] == "Independent":
                continue
            elif location["Brand"] == "Ampcharge":
                apply_category(Categories.CHARGING_STATION, item)
            elif location["Brand"] == "EG Ampol":
                set_operator(EG, item)
                apply_category(Categories.FUEL_STATION, item)
            elif location["Brand"] in ["The Foodary", "Ampol"]:
                apply_category(Categories.FUEL_STATION, item)
            else:
                self.logger.error("Unexpected brand: {}".format(location["Brand"]))

            item["opening_hours"] = OpeningHours()
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                if location[f"{day}_AllDay"]:
                    item["opening_hours"].add_range(day, "00:00", "23:59")
                else:
                    item["opening_hours"].add_range(
                        day,
                        location[f"{day}_Openning"].replace("Midnight", "00:00"),
                        location[f"{day}_Closing"].replace("Midnight", "23:59"),
                    )

            apply_yes_no(Fuel.E10, item, location["E10"], False)
            apply_yes_no(Fuel.OCTANE_91, item, location["ULP"], False)
            apply_yes_no(Fuel.OCTANE_95, item, location["VX95"] or location["PULP"], False)
            apply_yes_no(Fuel.OCTANE_98, item, location["VX98"] or location["SPULP"], False)
            apply_yes_no(Fuel.LPG, item, location["LPG"], False)
            apply_yes_no(Fuel.DIESEL, item, location["DSL"] or location["VXDSL"] or location["ATDSL"], False)
            apply_yes_no(Fuel.ADBLUE, item, location["ADBLU"], False)
            apply_yes_no(Fuel.PROPANE, item, location["BBQGas"], False)

            yield item
