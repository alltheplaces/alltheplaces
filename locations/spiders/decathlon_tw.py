from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class DecathlonTWSpider(Spider):
    name = "decathlon_tw"
    item_attributes = {"brand": "Decathlon", "brand_wikidata": "Q509349"}
    start_urls = ["https://www.decathlon.tw/api/store-setting?countryCode=TW"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            store.update(store.pop("address"))
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street")
            item["branch"] = item.pop("name").strip("店")
            yield item
