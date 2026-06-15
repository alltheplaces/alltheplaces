import html
import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class MitsubishiHRSpider(Spider):
    name = "mitsubishi_hr"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi-motors.hr/"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw = re.search(r'data-makers="(\[\[.*?\]\])"', response.text)
        if not raw:
            return
        for entry in json.loads(html.unescape(raw.group(1))):
            name, address, lat, lon = entry[0], entry[1], entry[2], entry[3]
            parts = re.split(r"<br\s*/?>", address)
            item = Feature()
            item["branch"] = name
            item["lat"] = lat
            item["lon"] = lon
            if len(parts) == 2:
                item["city"] = parts[0].strip()
                item["street_address"] = parts[1].strip()
            else:
                item["addr_full"] = address.strip()
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item
