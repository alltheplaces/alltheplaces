from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class DunelmGBSpider(scrapy.Spider):
    name = "dunelm_gb"
    item_attributes = {
        "brand": "Dunelm",
        "brand_wikidata": "Q5315020",
    }
    start_urls = ["https://sloc-service.dunelm.com/api/v2/dunelm/stores/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["result"]:
            item = DictParser.parse(location)
            item["ref"] = location["sapSiteId"]
            item["street_address"] = merge_address_lines([item["street_address"], location["localArea"]])
            item["website"] = "https://www.dunelm.com/stores/" + location["uri"]
            apply_category(Categories.SHOP_INTERIOR_DECORATION, item)
            yield item
