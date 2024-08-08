from urllib.parse import urlencode

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class IndigoSpider(scrapy.Spider):
    name = "indigo"
    item_attributes = {"operator": "Indigo", "operator_wikidata": "Q3559970"}
    url = "https://salesforce.parkindigo.com/locations?"

    def start_requests(self):
        params = {
            "location.language": "en",
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
            apply_category(Categories.PARKING, item)
            yield item

        if not data.get("last"):
            params = {
                "location.language": "en",
                "page": int(data.get("number")) + 1,
            }
            yield scrapy.Request(self.url + urlencode(params), callback=self.parse)
