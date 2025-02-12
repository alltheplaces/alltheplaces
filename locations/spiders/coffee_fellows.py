import json
import re
from typing import Any, Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class CoffeeFellowsSpider(scrapy.Spider):
    name = "coffee_fellows"
    item_attributes = {"brand": "Coffee Fellows", "brand_wikidata": "Q23461429", "extras": Categories.CAFE.value}
    start_urls = ["https://coffee-fellows.com/locations"]
    RE_TIME = re.compile(r"(\d\d):00")

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        raw_json = json.loads(response.xpath('//script[@type="application/json"]/text()').get())
        data = json.loads(raw_json["props"]["pageProps"]["page"])["locations"]
        for location in data:
            location["street_address"] = location.pop("street")
            location["lon"] = location["geocode"]["lng"]
            location["lat"] = location["geocode"]["lat"]
            location["image"] = location.pop("coverImage")
            item = DictParser.parse(location)
            item["opening_hours"] = self.format_opening_hours(location)
            item["extras"]["start_date"] = location["openingDate"].replace("T00:00:00.000Z", "")
            apply_yes_no("payment:credit_cards", item, location["hasCreditCard"])
            apply_yes_no("outdoor_seating", item, location["hasSeatsOutside"])
            apply_yes_no("wheelchair", item, location["isAccessible"])
            yield item

    def format_opening_hours(self, store: dict) -> OpeningHours:
        hours = OpeningHours()
        for weekday in DAYS_FULL:
            weekday = weekday.lower()
            if not store[f"{weekday}IsClosed"]:
                open_time = store[weekday]["open"]
                close_time = store[weekday]["close"]
                hours.add_range(weekday, open_time, close_time)
        return hours
