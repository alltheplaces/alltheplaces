from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class CosmoJPSpider(Spider):
    name = "cosmo_jp"

    start_urls = ["https://map.cosmo-energy.co.jp/api/points"]
    allowed_domains = ["shop.big-echo.jp"]
    item_attributes = {
        "brand_wikidata": "Q2498318",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["items"]:
            store.update(store.pop("extra_fields"))
            item = DictParser.parse(store)

            item["branch"] = store.get("name")
            item["website"] = f"https://map.cosmo-energy.co.jp/points/{store.get('key')}"
            item["ref"] = store.get("key")

            yield item
