# -*- coding: utf-8 -*-
import scrapy
from locations.dict_parser import DictParser
from locations.geo import postal_regions


class SparGBSpider(scrapy.Spider):
    name = "spar_gb"
    item_attributes = {
        "brand": "SPAR",
        "brand_wikidata": "Q610492",
        "country": "GB",
    }
    download_delay = 0.5

    def start_requests(self):
        url_template = (
            "https://www.spar.co.uk/umbraco/api/storelocationapi/stores?location={}"
        )
        for record in postal_regions("GB"):
            yield scrapy.Request(url_template.format(record["postal_region"]))

    def parse(self, response):
        for store in response.json()["storeList"]:
            item = DictParser.parse(store)
            item["website"] = "https://www.spar.co.uk" + store["StoreUrl"]
            item["street_address"] = store.get("Address1")
            yield item
