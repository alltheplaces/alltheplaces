# -*- coding: utf-8 -*-
import scrapy
import json
from locations.brands import Brand
from locations.seo import get_first_key, extract_details


class McCollsUKSpider(scrapy.Spider):
    name = "mccolls_uk"
    brand = Brand.from_wikidata("McColl's", "Q16997477")
    allowed_domains = ["mccolls.co.uk"]
    start_urls = ["https://www.mccolls.co.uk/storelocator/"]

    def parse(self, response):
        script = json.loads(
            response.xpath('//script[contains(., "allStores")]/text()').get()
        )
        for store in get_first_key(script, "items"):
            if store["store_type"] in ["NEWSAGENT", "CONVENIENCE", "CONVENIENCE PLUS"]:
                item = self.brand.item(store["store_url"])
                item["street_address"] = store.get("address")
                yield extract_details(item, store)
