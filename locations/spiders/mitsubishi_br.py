from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class MitsubishiBRSpider(scrapy.Spider):
    name = "mitsubishi_br"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://api.mitsubishimotors.com.br/search/api/dealer/v1.0/nearest?page=0&size=1000"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for dealer in response.json().get("results", []):
            item = DictParser.parse(dealer)
            item["branch"] = item.pop("name")
            website = dealer.get("website")
            if website and not website.startswith("https"):
                item["website"] = "https://" + website.strip()
            if dealer.get("newCars"):
                apply_category(Categories.SHOP_CAR, item)
            elif not dealer.get("newCars") and dealer.get("kitCarParts"):
                apply_category(Categories.SHOP_CAR_PARTS, item)
            yield item
