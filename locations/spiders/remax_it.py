import re

import scrapy

from locations.dict_parser import DictParser


class RemaxITSpider(scrapy.Spider):
    name = "remax_it"
    item_attributes = {
        "brand": "RE/MAX",
        "brand_wikidata": "Q965845",
    }
    allowed_domains = ["remax.com"]
    start_urls = ["https://cms.remax.it/api/v1/agencies?collection=false&commercial=false&page=1&per_page=1000"]

    def parse(self, response):
        for data in response.json()["agencies"]:
            item = DictParser.parse(data)
            item["lat"] = data.get("coordinates", {})[1]
            item["lon"] = data.get("coordinates", {})[0]
            item["phone"] = data.get("phone_nr")
            item["state"] = (re.findall("[A-Z]{2}", item["addr_full"])[0:1] or (None,))[0]
            item["postcode"] = (re.findall("[0-9]{5}|[A-Z0-9]{3} [A-Z0-9]{3}", item["addr_full"])[0:1] or (None,))[0]

            yield item
