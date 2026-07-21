import re
from typing import Any

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class HpbHRSpider(Spider):
    name = "hpb_hr"
    item_attributes = {"brand": "Hrvatska poštanska banka", "brand_wikidata": "Q5923981"}
    start_urls = ["https://www.hpb.hr/en/map/2752"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The map page embeds all locations as a `var markers = [...]` JS array.
        raw = response.text.split("var markers =", 1)[1]
        for location in parse_js_object(raw[raw.index("[") :]):
            if location.get("type") == "POSTA":
                continue  # Croatian Post offices, not HPB locations
            if not (location.get("latitude") and location.get("longitude")):
                continue

            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full", None)
            # The city field embeds the postcode, e.g. "10 000 Zagreb".
            if postcode_city := re.match(r"\s*(\d[\d ]*\d)\s+(.+)", item.get("city") or ""):
                item["postcode"] = postcode_city.group(1).replace(" ", "")  # "10 000" -> "10000"
                item["city"] = postcode_city.group(2)

            if location["type"] == "BANKOMAT":
                apply_category(Categories.ATM, item)
            else:  # POSLOVNICA, PODRUŽNICA, ISPOSTAVA
                item["branch"] = item.pop("name", None)
                apply_category(Categories.BANK, item)

            yield item
