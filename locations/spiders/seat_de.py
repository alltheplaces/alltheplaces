from copy import deepcopy

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SeatDESpider(scrapy.Spider):
    name = "seat_de"
    item_attributes = {"brand": "Seat", "brand_wikidata": "Q188217"}
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
            item["website"] = data.get("URL")
            item["email"] = data.get("EMAIL")
            if data.get("HAENDLERVERTRAG") == "J":
                shop_item = deepcopy(item)
                shop_item["ref"] = f"{item['ref']}-SHOP"
                apply_category(Categories.SHOP_CAR, shop_item)
                yield shop_item
            if data.get("SERVICEPARTNERVERTRAG") == "J":
                service_item = deepcopy(item)
                service_item["ref"] = f"{item['ref']}-SERVICE"
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item
