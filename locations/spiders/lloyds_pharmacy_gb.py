import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.sainsburys import SainsburysSpider


class LloydsPharmacyGBSpider(scrapy.Spider):
    name = "lloyds_pharmacy_gb"
    item_attributes = {"brand": "Lloyds Pharmacy", "brand_wikidata": "Q6662870"}
    start_urls = ["https://store-locator.lloydspharmacy.com/store-locator"]

    def parse(self, response):
        for store in response.json()["stores"]:
            item = DictParser.parse(store)

            oh = OpeningHours()
            for day, times in store["hours"].items():
                if len(times) == 2:
                    oh.add_range(day, times[0], times[1])
            item["opening_hours"] = oh.as_opening_hours()

            address = store["address"]
            town = address["town"]
            locality = address["locality"]

            if locality and locality != town:
                if town:
                    city = town
                    addr = ", ".join([address["street"], locality])
                else:
                    city = locality
                    addr = address["street"]
            else:
                city = town
                addr = address["street"]

            item["street_address"] = addr
            item["street"] = None
            item["city"] = city

            if "Sainsburys" in item["name"]:
                item["located_in"] = SainsburysSpider.item_attributes["brand"]
                item["located_in_wikidata"] = SainsburysSpider.item_attributes["brand_wikidata"]

            yield item
