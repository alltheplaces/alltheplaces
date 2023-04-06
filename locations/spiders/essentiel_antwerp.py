import json
import re

import scrapy

from locations.items import Feature


class EssentielAntwerpSpider(scrapy.Spider):
    name = "essentiel_antwerp"
    item_attributes = {"brand": "Essentiel Antwerp", "brand_wikidata": "Q117456339"}
    start_urls = ["https://www.essentiel-antwerp.com/be_fr/storelocator"]

    def parse(self, response):
        data = response.text
        stores = json.loads(re.search(r"stores:(\[.*\])", data).group(1))
        for store in stores:
            item = Feature()
            item["ref"] = store["storelocator_id"]
            item["phone"] = store["phone"]
            item["country"] = store["country"]
            item["state"] = store["state"]
            item["postcode"] = store["zipcode"]
            item["lat"] = float(store["latitude"])
            item["lon"] = float(store["longtitude"])
            item["street_address"] = store["address"]
            item["city"] = store["city"]
            item["name"] = "Essentiel Antwerp" + " " + store["rewrite_request_path"].replace("-", " ").title()
            item["website"] = f'https://www.essentiel-antwerp.com/eu/{store["rewrite_request_path"]}/'
            yield item
