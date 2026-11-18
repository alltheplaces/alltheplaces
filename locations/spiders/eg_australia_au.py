import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours

AMPOL = {"name": "Ampol", "brand": "Ampol", "brand_wikidata": "Q4748528"}
EG = {"brand": "EG Australia", "brand_wikidata": "Q5023980"}
FUELS = {
    1: Fuel.OCTANE_91,
    2: Fuel.OCTANE_95,
    3: Fuel.OCTANE_98,
    4: Fuel.DIESEL,
    6: Fuel.DIESEL,
    10: Fuel.E10,
    11: Fuel.LPG,
}


class EgAustraliaAUSpider(Spider):
    name = "eg_australia_au"
    item_attributes = {"operator": "EG Australia", "operator_wikidata": "Q5023980"}
    start_urls = ["https://eg-australia.com/eg-store-locator/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            url="https://eg-australia.com/wp-admin/admin-ajax.php?lat=0&lng=0&action=search_stores&nonce={}".format(
                re.search(r"\"ajax_nonce\":\"(.+?)\"", response.text).group(1)
            ),
            callback=self.parse_api,
        )

    def parse_api(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["stores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            apply_yes_no(Extras.TOILETS, item, 11 in location["features"])

            item["opening_hours"] = OpeningHours()
            for rule in location["fullHours"]:
                open_time = rule["minutesFromMidnightOpen"]
                close_time = rule["minutesFromMidnightClose"] or 24 * 60
                for bit, day in enumerate(DAYS[-1:] + DAYS[:-1]):
                    if rule["days"] & (1 << bit):
                        item["opening_hours"].add_range(
                            day,
                            f"{open_time // 60:02d}:{open_time % 60:02d}",
                            f"{close_time // 60:02d}:{close_time % 60:02d}",
                        )

            if location["bannerId"] & 4 == 4:
                ampol = item.deepcopy()
                ampol.update(AMPOL)
                for price in location["prices"]:
                    if fuel := FUELS.get(price["id"]):
                        apply_yes_no(fuel, ampol, True)
                apply_category(Categories.FUEL_STATION, ampol)
                yield ampol
            if location["bannerId"] & 3 == 3:
                eg = item.deepcopy()
                eg["ref"] = "{}-eg".format(item["ref"])
                eg.update(EG)
                apply_category(Categories.SHOP_CONVENIENCE, eg)
                yield eg
