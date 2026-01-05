import re
from typing import Any

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class EkominiTRSpider(Spider):
    name = "ekomini_tr"
    item_attributes = {"brand": "Ekomini", "brand_wikidata": "Q115534014"}
    start_urls = ["https://www.ekomini.com.tr/magazalar"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location_js in re.findall(r"map\.addMarker\(({.+?})\);", response.text, re.DOTALL):
            location = chompjs.parse_js_object(location_js)
            if location["title"] == "Sizin Konumunuz":
                continue

            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("EKOMİNİ").strip("- ")

            sel = Selector(text=location["infoWindow"]["content"])

            item["website"] = item["ref"] = response.urljoin(sel.xpath("//a/@href").get())
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
