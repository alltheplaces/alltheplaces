from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class ClintonsGBSpider(scrapy.Spider):
    name = "clintons_gb"
    item_attributes = {"brand": "Clintons", "brand_wikidata": "Q5134299"}
    start_urls = ["https://www.clintonscards.co.uk/wp-json/store-locations/v1/search"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["link"]
            item["street_address"] = merge_address_lines([location["address2"], item.pop("addr_full")])
            yield item
