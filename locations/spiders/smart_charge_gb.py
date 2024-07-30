from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

SOCKET_MAP = {
    "Chademo": "chademo",
    "IEC_62196_T2_Combo": "type2_combo",
}


class SmartChargeGBSpider(Spider):
    name = "smart_charge_gb"
    item_attributes = {"brand": "Smart Charge", "brand_wikidata": "Q127686420"}
    start_urls = ["https://smartcharge.co.uk/api/locations"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if location["status"] == "Announced":
                continue

            item = DictParser.parse(location)
            item.pop("addr_full", None)

            if max_power := location.get("maxPowerKw"):
                item["extras"]["charging_station:output"] = "{} kW".format(max_power)

            for socket in location["evseInformation"]:
                if m := SOCKET_MAP.get(socket["type"]):
                    item["extras"]["socket:{}".format(m)] = str(socket["totalEvses"])

            apply_category(Categories.CHARGING_STATION, item)

            yield item
