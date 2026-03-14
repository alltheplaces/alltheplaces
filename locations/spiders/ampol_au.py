import re
from typing import Any

import scrapy
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.central_england_cooperative import set_operator
from locations.user_agents import BROWSER_DEFAULT

EG = {"brand": "EG Australia", "brand_wikidata": "Q5023980"}


class AmpolAUSpider(Spider):
    name = "ampol_au"
    item_attributes = {"brand": "Ampol", "brand_wikidata": "Q4748528"}
    allowed_domains = ["www.ampol.com.au", "digital-api.ampol.com.au"]
    start_urls = ["https://www.ampol.com.au/find-a-service-station"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        js_url = response.xpath('//*[contains(@src,"route")]/@src').get()
        yield scrapy.Request(url="https://www.ampol.com.au" + js_url, callback=self.parse_token)

    def parse_token(self, response):
        token = re.search(r"Ocp-Apim-Subscription-Key\"\s*:\s*\"([a-z0-9]+)", response.text).group(1)
        yield JsonRequest(
            url="https://digital-api.ampol.com.au/siteservice/Service/",
            headers={"ocp-apim-subscription-key": token},
            callback=self.parse_details,
        )

    def parse_details(self, response):
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
