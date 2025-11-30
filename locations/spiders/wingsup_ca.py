import re
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class WingsupCASpider(Spider):
    name = "wingsup_ca"
    item_attributes = {"brand": "WingsUp!", "brand_wikidata": "Q137167877"}
    start_urls = ["https://wingsup.com/Locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            re.search(r"var locations = (\[.+])", response.text, re.DOTALL).group(1)
        ):
            item = Feature()

            if m := re.match(r"<div class=\"map-window\"><strong>(.+)</strong><br/>(.+)</div>", location[0]):
                if "Coming Soon" in m.group(1):
                    continue
                item["branch"] = m.group(1).replace("NOW OPEN", "").strip(" !-")
                item["addr_full"] = m.group(2)

            item["ref"] = location[3]
            item["lat"] = location[1]
            item["lon"] = location[2]

            apply_category(Categories.FAST_FOOD, item)
            yield item
