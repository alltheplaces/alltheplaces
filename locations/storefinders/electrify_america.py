import copy
import re

import scrapy

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.json_blob_spider import JSONBlobSpider

SOCKET_TYPES = {
    "CHADEMO": "chademo",
    "IEC_62196_T1": "type1",
    "IEC_62196_T1_COMBO": "type1_combo",
    "SAE_J3400": "nacs",
}


class ElectrifyAmericaSpider(JSONBlobSpider):
    """Base class for Electrify America and Electrify Canada"""

    domain: str

    async def start(self):
        yield scrapy.Request(f"https://api-prod.{self.domain}/v2/locations")

    def post_process_item(self, item, response, feature):
        apply_category(Categories.CHARGING_STATION, item)
        item["street_address"] = item.pop("addr_full")

        station_type = feature.get("type")
        if station_type == "PUBLIC":
            item["extras"]["access"] = "public"
        elif station_type == "COMMERCIAL":
            item["extras"]["access"] = "customers"
        elif station_type == "COMING_SOON":
            return

        city_slug = re.sub(r"\s", "-", feature["city"]).lower()
        address_slug = re.sub(r"[<>#%|'’.]", "", re.sub(r"\s", "-", feature["address"])).lower()
        # The /-/ is supposed to be the state abbreviation, but we only have the full state name.
        # The placeholder results in an extra redirect.
        item["website"] = f"https://www.{self.domain}/locate-charger/-/{city_slug}/{address_slug}/{feature['id']}/"

        yield item

        yield scrapy.Request(
            f"https://api-prod.{self.domain}/v2/locations/{feature['id']}", callback=self.parse_charge_points
        )

    def parse_charge_points(self, response):
        parent = DictParser.parse(response.json())
        apply_category(Categories.CHARGE_POINT, parent)
        parent["street_address"] = parent.pop("addr_full")

        station_type = response.json().get("type")
        if station_type == "PUBLIC":
            parent["extras"]["access"] = "public"
        elif station_type == "COMMERCIAL":
            parent["extras"]["access"] = "customers"

        for feature in response.json().get("evses", []):
            item = copy.deepcopy(parent)
            item["ref"] = feature["id"]

            for connector in feature.get("connectors", []):
                socket_type = SOCKET_TYPES[connector.get("standard")]
                apply_yes_no(f"socket:{socket_type}", item, True)
                item["extras"][f"socket:{socket_type}:current"] = str(connector["amperage"])
                item["extras"][f"socket:{socket_type}:voltage"] = str(connector["voltage"])
                item["extras"][
                    f"socket:{socket_type}:output"
                ] = f"{round(connector['amperage'] * connector['voltage'] / 1000)} kW"

            yield item
