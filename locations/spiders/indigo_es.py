import json
from urllib.parse import urlencode

import scrapy

from locations.dict_parser import DictParser


class IndigoESSpider(scrapy.Spider):
    name = "indigo_es"
    item_attributes = {"brand": "Indigo", "brand_wikidata": "Q3559970"}
    url = "https://salesforce.parkindigo.com/locations?"
    bbox = (-9.39288367353, 35.946850084, 3.03948408368, 43.7483377142)

    def start_requests(self):
        params = {
            "location.language": "en",
            "location.address.countries": self.name[-2:].upper(),
            "box.first.x": self.bbox[3],
            "box.first.y": self.bbox[0],
            "box.second.x": self.bbox[1],
            "box.second.y": self.bbox[2],
            "page": 0,
        }
        yield scrapy.Request(self.url + urlencode(params))

    def parse(self, response):
        data = response.json()
        for lot in data["content"]:
            item = DictParser.parse(lot)
            item["extras"]["capacity"] = lot.get("totalSpaces", None)
            item["lat"] = lot.get("geoLocation", {}).get("x")
            item["lon"] = lot.get("geoLocation", {}).get("y")
            item["street_address"] = lot.get("address", {}).get("lines", [None])[0]
            yield item

        if not data.get("last"):
            params = {
                "location.language": "en",
                "location.address.countries": self.name[-2:].upper(),
                "box.first.x": self.bbox[3],
                "box.first.y": self.bbox[0],
                "box.second.x": self.bbox[1],
                "box.second.y": self.bbox[2],
                "page": int(data.get("number")) + 1,
            }
            yield scrapy.Request(self.url + urlencode(params), callback=self.parse)
