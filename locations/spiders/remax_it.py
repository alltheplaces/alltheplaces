import json
import re

import scrapy

from locations.dict_parser import DictParser


class RemaxITSpider(scrapy.Spider):
    name = "remax_it"
    item_attributes = {
        "brand": "RE/MAX",
        "brand_wikidata": "Q965845",
    }
    allowed_domains = ["www.remax.it"]
    start_urls = ["https://www.remax.it/agenzie"]

    def parse(self, response):
        json_data = json.loads(
            re.search(
                r"mapAgencies\":(\[.+\]),\"source\":\"net",
                response.xpath('//*[contains(text(),"postalCode")]/text()').get().replace("\\", ""),
            ).group(1)
        )
        for data in json_data:
            item = DictParser.parse(data)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name").removeprefix("The REMAX Collection ").removeprefix("REMAX ")
            item["website"] = f"https://{data.get('l1Slug')}.remax.it/agenzia"

            yield item
