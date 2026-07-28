import re
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.equinox import EquinoxSpider
from locations.spiders.tesco_gb import set_located_in


class JuicePressUSSpider(Spider):
    name = "juice_press_us"
    item_attributes = {"brand": "Juice Press", "brand_wikidata": "Q27150131"}
    start_urls = ["https://www.juicepress.com/pages/location"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = list(
            chompjs.parse_js_objects(
                re.search(r"JPSTORELOCATOR\.locations\.push\((.*)\);Object", response.text, re.DOTALL).group(1)
            )
        )
        for store in raw_data:
            item = DictParser.parse(store)
            item["addr_full"] = None
            item["street_address"] = item.pop("name")
            item["image"] = store["image"]
            item["ref"] = store["selector"]

            if float(item["lon"]) > 0:
                item["lon"] = float(item["lon"]) * -1

            if "Equinox" in item["street_address"]:
                set_located_in(EquinoxSpider.item_attributes, item)

            # NSI's single entry for this brand is scoped to only a few US
            # states/a city, so most locations need the category applied
            # directly rather than relying on NSI's location matching.
            apply_category(Categories.FAST_FOOD, item)

            yield item
