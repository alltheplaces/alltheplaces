from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser


class AsicsEUSpider(scrapy.Spider):
    name = "asics_eu"
    item_attributes = {"brand": "ASICS", "brand_wikidata": "Q327247"}
    allowed_domains = ["www.asics.com"]
    start_urls = ["https://cdn.crobox.io/content/ujf067/stores.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            if store["storetype"] in ["factory-outlet", "retail-store"]:
                item = DictParser.parse(store)
                item["street_address"] = item.pop("addr_full")
                item["ref"] = store["name"]
                yield item
