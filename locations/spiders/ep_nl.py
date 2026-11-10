import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class EpNLSpider(Spider):
    name = "ep_nl"
    item_attributes = {"brand": "EP:", "brand_wikidata": "Q110271192"}
    start_urls = ["https://www.ep.nl/winkels"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The store list is embedded in the Next.js payload with escaped quotes
        text = response.text.replace(r"\"", '"')

        marker = '"stores":'
        idx = text.find(marker)
        if idx == -1:
            return

        try:
            stores, _ = json.JSONDecoder().raw_decode(text, idx + len(marker))
        except json.JSONDecodeError:
            return

        for store in stores:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name").removeprefix("EP:").strip()
            item["name"] = self.item_attributes["brand"]
            item["street_address"] = item.pop("addr_full")
            item["website"] = store.get("domain")
            apply_category(Categories.SHOP_ELECTRONICS, item)

            yield item
