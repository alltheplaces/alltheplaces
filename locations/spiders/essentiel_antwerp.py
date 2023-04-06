import json
import re

import scrapy

from locations.items import Feature


class EssentielAntwerpSpider(scrapy.Spider):
    name = "essentiel_antwerp"
    item_attributes = {"brand": "Essentiel-Antwerp"}
    start_urls = ["https://www.essentiel-antwerp.com/be_fr/storelocator"]

    def parse(self, response):
        data = response.xpath(".").get()
        stores = json.loads("[" + re.findall(r"(stores:\[)(.*?)(])", data)[0][1] + "]")
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
            item["name"] = "Essentiel-Antwerp" + " ".join(store["rewrite_request_path"].split("-"))
            yield item
