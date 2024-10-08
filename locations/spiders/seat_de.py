import scrapy

from locations.dict_parser import DictParser


class SeatDESpider(scrapy.Spider):
    name = "seat_de"
    item_attributes = {
        "brand": "SEAT",
        "brand_wikidata": "Q188217",
    }
    allowed_domains = ["seat.de"]
    start_urls = ["https://haendlersuche.seat.de///tmp/b93b5efda7f2cc5a13f0ae5bbb3c9981.cache"]

    def parse(self, response):
        for data in response.json().get("allDealers", {}).get("v"):
            item = DictParser.parse(data)
            item["ref"] = data.get("NUMMER")
            item["name"] = data.get("NAME1")
            item["phone"] = data.get("TELEFON")
            item["street"] = data.get("STRA\u00dfE")
            item["city"] = data.get("ORT")
            item["postcode"] = data.get("PLZ")
            item["lat"] = data.get("XPOS")
            item["lon"] = data.get("YPOS")

            yield item
