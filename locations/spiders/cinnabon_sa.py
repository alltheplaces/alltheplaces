from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class CinnabonSASpider(Spider):
    name = "cinnabon_sa"
    item_attributes = {"brand": "Cinnabon", "brand_wikidata": "Q1092539"}
    start_urls = ["https://cinnabon-ksa.com/wp-admin/admin-ajax.php?action=asl_load_stores&nonce=84b9278c6c&load_all=1"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for shop in response.json():
            item = DictParser.parse(shop)
            item["street_address"] = item.pop("street")
            item["website"] = "https://cinnabon-ksa.com/"
            yield item
