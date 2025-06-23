from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class BigLotsUSSpider(Spider):
    name = "big_lots_us"
    item_attributes = {"brand": "Big Lots", "brand_wikidata": "Q4905973"}
    start_urls = [
        "https://core.service.elfsight.com/p/boot/?page=https%3A%2F%2Fbiglots.com%2Fstore-locator%2F&w=38636f5f-4115-4585-8c00-9e245fd92818"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["widgets"]["38636f5f-4115-4585-8c00-9e245fd92818"]["data"]["settings"][
            "locations"
        ]:
            location.update(location.pop("place"))
            item = DictParser.parse(location)
            item.pop("website")
            yield item
