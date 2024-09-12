import re
from typing import Any

import chompjs

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.avia_de import AVIA_SHARED_ATTRIBUTES


class AviaHUSpider(JSONBlobSpider):
    name = "avia_hu"
    item_attributes = AVIA_SHARED_ATTRIBUTES
    start_urls = ["https://www.avia.hu/kapcsolat/toltoallomasok/"]

    def extract_json(self, response):
        return chompjs.parse_js_object(re.search(r"var markers = (\[.+?\]);", response.text, re.DOTALL).group(1))

    def pre_process_data(self, location) -> Any:
        location["ref"] = location.pop("kutid")
        location["branch"] = location.pop("title")
        location["addr_full"] = location.pop("cim")
        location["website"] = "https://www.avia.hu/toltoallomas/?id={}".format(location["ref"])
        location["tel"] = location["tel"].replace(",", "; ")

    def post_process_item(self, item, response, location):
        apply_yes_no(Fuel.OCTANE_95, item, location["b95"] == "1" or location["b95g"] == "1")
        apply_yes_no(Fuel.DIESEL, item, location["dies"] == "1" or location["gdies"] == "1")
        apply_yes_no(Fuel.OCTANE_98, item, location["b98"] == "1")
        apply_yes_no(Fuel.LPG, item, location["lpg"] == "1")
        apply_yes_no(Fuel.E85, item, location["e85"] == "1")
        apply_yes_no("rent:lpg_bottles", item, location["pgaz"] == "1")
        apply_yes_no(Extras.COMPRESSED_AIR, item, location["komp"] == "1")
        apply_yes_no("restaurant", item, location["etterem"] == "1")
        apply_yes_no("food", item, location["bufe"] == "1")
        apply_yes_no("hgv", item, location["kpark"] == "1")

        apply_category(Categories.FUEL_STATION, item)

        yield item
