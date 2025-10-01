import json
import re
from typing import Any, Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class CoffeeFellowsSpider(scrapy.Spider):
    name = "coffee_fellows"
    item_attributes = {"brand": "Coffee Fellows", "brand_wikidata": "Q23461429"}
    start_urls = ["https://coffee-fellows.com/locations"]
    RE_TIME = re.compile(r"(\d\d):00")

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        raw_json = json.loads(response.xpath('//script[@type="application/json"]/text()').get())
        data = json.loads(raw_json["props"]["pageProps"]["page"])["locations"]
        for location in data:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street")
            item["lon"] = location["geocode"]["lng"]
            item["lat"] = location["geocode"]["lat"]
            item["image"] = location.pop("coverImage")
            item["branch"] = item.pop("name")
            item["opening_hours"] = self.format_opening_hours(location)
            if opening_date := location.get("openingDate"):
                item["extras"]["start_date"] = opening_date.replace("T00:00:00.000Z", "")
            apply_yes_no(PaymentMethods.CREDIT_CARDS, item, location["hasCreditCard"])
            apply_yes_no(Extras.OUTDOOR_SEATING, item, location["hasSeatsOutside"])
            apply_yes_no(Extras.WHEELCHAIR, item, location["isAccessible"])

            apply_category(Categories.CAFE, item)

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
