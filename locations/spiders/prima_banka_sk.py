from typing import Any

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser

REGIONS = [
    "banskobystricky-kraj",
    "bratislavsky-kraj",
    "kosicky-kraj",
    "nitriansky-kraj",
    "presovsky-kraj",
    "trenciansky-kraj",
    "trnavsky-kraj",
    "zilinsky-kraj",
]


class PrimaBankaSKSpider(Spider):
    name = "prima_banka_sk"
    item_attributes = {"brand": "Prima banka", "brand_wikidata": "Q13538661"}
    start_urls = [f"https://www.primabanka.sk/pobocky-a-bankomaty/{region}" for region in REGIONS]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Each region page embeds its locations as a `var markers = [...]` JS array.
        raw = response.text.split("var markers =", 1)[1]
        for location in parse_js_object(raw[raw.index("[") :]):
            location_type = location["type"]

            item = DictParser.parse(location)
            item.pop("state", None)  # source "state" is a status flag, not a region
            item.pop("email", None)  # a single generic address, not location-specific
            item["lat"] = location["gps_lat"]
            item["lon"] = location["gps_lon"]
            item["addr_full"] = location.get("adresa")  # free-form (landmarks/districts), so not street_address
            item["city"] = location.get("mesto")
            item["postcode"] = location.get("psc")

            if location_type == "bankomat":
                apply_category(Categories.ATM, item)
            elif location_type in ("pobocka", "firemne_centrum"):
                item["branch"] = item.pop("name", None)
                apply_yes_no(Extras.ATM, item, location.get("ma_bankomat") == "1")
                apply_category(Categories.BANK, item)
            else:
                self.logger.error("Unexpected location type: {}".format(location_type))
                continue

            yield item
