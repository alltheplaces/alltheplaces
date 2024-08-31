import scrapy

from locations.dict_parser import DictParser


class WolleRodelDESpider(scrapy.Spider):
    item_attributes = {
        "brand_wikidata": "Q107357091",
        "brand": "Wolle Rödel",
    }
    name = "wolle_rodel_de"
    allowed_domains = ["www.wolle-roedel.com"]
    start_urls = ["https://www.wolle-roedel.com/StoreLocator/getStores"]

    def parse(self, response):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["ref"] = location["_uniqueIdentifier"]
            item["name"] = location["label"]
            item["website"] = "https://www.wolle-roedel.com/" + location["translated"]["seoUrl"]
            # TODO: location["extensions"] contains business hours, but the days of the week are keys like '1dd4f7f0b2094a909f0d3cda1acd9be4'
            yield item
