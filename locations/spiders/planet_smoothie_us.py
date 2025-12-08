import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PlanetSmoothieUSSpider(Spider):
    name = "planet_smoothie_us"
    item_attributes = {"brand": "Planet Smoothie", "brand_wikidata": "Q7201170"}
    start_urls = ["https://www.planetsmoothie.com/locator/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location_raw in re.findall(r"Locator\.stores\[\d+\] = ({.+})", response.text):
            location = json.loads(location_raw)
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full")
            item["website"] = "https://www.planetsmoothie.com/stores/{}/{}".format(
                location["cleanCity"], location["StoreId"]
            )
            apply_category(Categories.FAST_FOOD, item)
            yield item
