import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser

AMPOL = {"name": "Ampol", "brand": "Ampol", "brand_wikidata": "Q4748528"}
EG = {"brand": "EG Australia", "brand_wikidata": "Q5023980"}


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
            if location["enabled"] is False:
                continue
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            apply_yes_no(Extras.TOILETS, item, 11 in location["features"])

            # TODO Fuels and opening hours available

            if location["bannerId"] & 4 == 4:
                ampol = item.deepcopy()
                ampol.update(AMPOL)
                apply_category(Categories.FUEL_STATION, ampol)
                yield ampol
            if location["bannerId"] & 3 == 3:
                eg = item.deepcopy()
                eg["ref"] = "{}-eg".format(item["ref"])
                eg.update(EG)
                apply_category(Categories.SHOP_CONVENIENCE, eg)
                yield eg
