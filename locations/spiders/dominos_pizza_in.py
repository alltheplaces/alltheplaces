import json
from typing import Iterator

import scrapy
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class DominosPizzaINSpider(Spider):
    name = "dominos_pizza_in"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    start_urls = ["https://www.dominos.co.in/store-location"]

    def parse(self, response: Response) -> Iterator[Feature]:
        for city in json.loads(response.xpath("//brand-city-list//@data-results").get()):
            yield scrapy.Request(url=f"https://www.dominos.co.in/store-location/{city}", callback=self.parse_city)

    def parse_city(self, response: Response) -> Iterator[Feature]:
        for stores_data in json.loads(response.xpath("//brand-store-list//@data-results").get()) or []:
            for store in stores_data.get("storeStationDetails") or []:
                if store["store"].get("storeOperationalTag") != "OPERATIONAL":
                    continue
                item = DictParser.parse(store.get("store"))
                item["branch"] = item.pop("name")
                item["website"] = response.url
                delivery_hours = OpeningHours()
                for station in store["store"].get("stations") or []:
                    if station["deliveryTypeCode"] == "D":
                        delivery_hours.add_days_range(DAYS, station["startTime"], station["endTime"], "%I:%M%p")
                if delivery_hours:
                    item["extras"]["opening_hours:delivery"] = delivery_hours.as_opening_hours()
                apply_category(Categories.FAST_FOOD, item)
                yield item
