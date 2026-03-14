import json

import scrapy

from locations.dict_parser import DictParser


class OmegawatchesSpider(scrapy.Spider):
    name = "omegawatches"
    item_attributes = {"brand": "Omega", "brand_wikidata": "Q659224"}
    allowed_domains = ["omegawatches.com"]
    start_urls = ["https://www.omegawatches.com/store"]

    def find_between(self, text, first, last):
        start = text.index(first) + len(first)
        end = text.index(last, start)
        return text[start:end]

    def parse(self, response):
        data = self.find_between(response.text, "var stores = ", "; var pm_countries = ").replace("];[", ",")
        json_data = json.loads(data)
        for storeid in json_data:
            data = json_data.get(storeid)
            item = DictParser.parse(data)
            if data.get("is_boutique"):
                item["email"] = data.get("contacts", {}).get("email")
                item["phone"] = data.get("contacts", {}).get("phone")
                item["street_address"] = data.get("adr").replace("<br />", " ")
                item["website"] = f'https://{self.allowed_domains[0]}/{data.get("websiteUrl")}'

                yield item
