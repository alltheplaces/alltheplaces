import json
from typing import Any

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.linked_data_parser import LinkedDataParser


class RymanGBSpider(Spider):
    name = "ryman_gb"
    item_attributes = {"brand": "Ryman", "brand_wikidata": "Q7385188"}
    start_urls = ["https://www.ryman.co.uk/storefinder/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripts = response.xpath('//script[@type="text/x-magento-init"]//text()').getall()
        for script in scripts:
            if "locations" in script:
                result = json.loads(script)
                for store in DictParser.get_nested_key(result, "locations"):
                    yield scrapy.Request(
                        store["store_url"],
                        callback=self.parse_store_page,
                        cb_kwargs=dict(store=store),
                    )

    def parse_store_page(self, response, store):
        if item := LinkedDataParser.parse(response, "Store"):
            item["lat"] = store["latitude"]
            item["lon"] = store["longitude"]
            item["branch"] = item.pop("name")
            yield item
