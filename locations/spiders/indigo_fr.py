import json
from urllib.parse import urlencode

import scrapy

from locations.dict_parser import DictParser


class IndigoFRSpider(scrapy.Spider):
    name = "indigo_fr"
    item_attributes = {"brand": "Indigo", "brand_wikidata": "Q3559970"}
    url = "https://salesforce.parkindigo.com/locations?"
    bbox = (-54.5247541978, 2.05338918702, 9.56001631027, 51.1485061713)

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
