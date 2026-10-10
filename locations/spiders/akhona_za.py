from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class AkhonaZASpider(Spider):
    name = "akhona_za"
    start_urls = ["https://www.akhonafurn.co.za/furniture-stores"]
    item_attributes = {"brand": "Akhona", "brand_wikidata": "Q116620476"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        js = response.xpath("//script[contains(text(), 'var S=')]/text()").re_first(r"var S=(\[.*?\]);")
        for location in chompjs.parse_js_object(js):
            item = Feature()
            item["ref"] = location["t"]
            if location["t"] == "Warehouse":
                apply_category(Categories.INDUSTRIAL_WAREHOUSE, item)
            else:
                item["branch"] = location["t"]
                apply_category(Categories.SHOP_FURNITURE, item)

            item["addr_full"] = location["a"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]

            yield item
