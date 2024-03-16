import re
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.spiders.avia_de import AVIA_SHARED_ATTRIBUTES


class AviaHUSpider(Spider):
    name = "avia_hu"
    item_attributes = AVIA_SHARED_ATTRIBUTES
    start_urls = ["https://www.avia.hu/kapcsolat/toltoallomasok/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            re.search(r"var markers = (\[.+?\]);", response.text, re.DOTALL).group(1)
        ):
            item = Feature()
            item["ref"] = location["kutid"]
            item["branch"] = location["title"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["addr_full"] = location["cim"]
            item["website"] = "https://www.avia.hu/toltoallomas/?id={}".format(item["ref"])
            item["phone"] = location["tel"].replace(",", "; ")
            item["email"] = location["email"]

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
