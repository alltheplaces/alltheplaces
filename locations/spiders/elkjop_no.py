from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class ElkjopNOSpider(Spider):
    name = "elkjop_no"
    item_attributes = {"name": "Elkjøp", "brand": "Elkjøp", "brand_wikidata": "Q1771628"}
    start_urls = ["https://www.elkjop.no/api/stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        res = response.json().get("data", {})
        for store in res.get("stores", []):
            item = DictParser.parse(store)

            item["branch"] = item.pop("name").removeprefix("Elkjøp ")

            if address := store.get("address"):
                item["housenumber"] = address.get("nr")
                if location := address.get("location"):
                    item["lat"] = location.get("lat")
                    item["lon"] = location.get("lng")

            if url := store.get("url"):
                item["website"] = urljoin("https://www.elkjop.no/", url)

            apply_category(Categories.SHOP_ELECTRONICS, item)

            yield item
