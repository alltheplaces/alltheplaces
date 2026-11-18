import json
import re

import scrapy

from locations.categories import apply_category
from locations.dict_parser import DictParser


class AureconGroupSpider(scrapy.Spider):
    name = "aurecon_group"
    item_attributes = {"brand": "Aurecon", "brand_wikidata": "Q2871849"}
    allowed_domains = ["www.aurecongroup.com"]
    start_urls = ("https://www.aurecongroup.com/contact-us",)

    def parse(self, response):
        data = json.loads(
            re.search(
                r"\"ContactCards\":\s*(\[.+\]),\s*\"ActiveLocationTagId\"",
                response.xpath('//*[contains(text(),"Latitude")]/text()').get(),
            ).group(1)
        )
        for location in data:
            if location.get("Address"):
                item = DictParser.parse(location)
                item["ref"] = item["addr_full"]
                apply_category({"office": "construction_company"}, item)
                yield item
