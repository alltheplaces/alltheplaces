from typing import Any, Iterable

import scrapy
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, Vending, add_vending, apply_category
from locations.dict_parser import DictParser


class RepontHUSpider(scrapy.Spider):
    name = "repont_hu"
    item_attributes = {
        "brand": "REpont",
        "brand_wikidata": "Q130348902",
        "operator": "MOHU MOL Hulladékgazdálkodási Zrt.",
        "operator_wikidata": "Q130207606",
    }
    start_urls = ["https://map.mohu.hu/api/Map/GetAllPois"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for poi in response.json():
            yield JsonRequest(
                f"https://map.mohu.hu/api/Map/GetWastePointDetails?id={poi['id']}", callback=self.parse_details
            )

    def parse_details(self, response: Response) -> Any:
        item = DictParser.parse(response.json())
        item["street_address"] = item.pop("addr_full")
        apply_category(Categories.VENDING_MACHINE, item)
        add_vending(Vending.BOTTLE_RETURN, item)
        yield item
