from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SkiptonGBSpider(scrapy.Spider):
    name = "skipton_gb"
    item_attributes = {"brand": "Skipton Building Society", "brand_wikidata": "Q16931747"}
    start_urls = ["https://www.skipton.co.uk/graphql/execute.json/sbs-sites/branchFinderList"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for bank in response.json()["data"]["branchFinderList"]["items"]:
            item = DictParser.parse(bank)
            item["ref"] = item["website"] = bank["moreLink"]
            item["addr_full"] = bank["address"]["plaintext"]
            item["branch"] = item.pop("name")
            apply_category(Categories.BANK, item)
            yield item
