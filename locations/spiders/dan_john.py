import re

import scrapy
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class DanJohnSpider(Spider):
    name = "dan_john"
    item_attributes = {"brand": "Dan John", "brand_wikidata": "Q116304215"}
    start_urls = ["https://stores.danjohn.com/it"]

    def parse(self, response, **kwargs):
        api_key = re.search(r"api_key\":\"(.+)\"};", response.text).group(1)
        yield scrapy.Request(
            url=f"https://api.retailtune.com/storelocator/it/?rt_api_key={api_key.strip()}",
            headers={"Origin": "https://stores.danjohn.com"},
            callback=self.parse_details,
        )

    def parse_details(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            if location["address2"]:
                item["street_address"] = merge_address_lines([location.get("address2"), item["street_address"]])
            item["branch"] = item.pop("name").replace("Dan John", "")
            item["state"] = location["province"]["name"]
            yield item
