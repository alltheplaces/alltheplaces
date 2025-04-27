import json

import scrapy

from locations.dict_parser import DictParser


class TuevNordDESpider(scrapy.Spider):

    name = "tuev_nord_de"
    item_attributes = {"brand": "TÜV Nord", "brand_wikidata": "Q2463547"}
    baseurl = ""
    start_urls = ["https://www.tuev-nord.de/de/privatkunden/tuev-stationen/"]

    def parse(self, response, **kwargs):
        data_locations = json.loads(response.xpath("//div/@data-locations").get())
        for location in data_locations:
            location["street_address"] = location.pop("address")
            location["zipcode"] = location.pop("plz")
            location["name"] = location.pop("station")
            location["ref"] = location["name"]
            location["website"] = response.urljoin(location.pop("link"))
            item = DictParser.parse(location)
            yield item
