import json
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature


class CooplandsGBSpider(Spider):
    name = "cooplands_gb"
    item_attributes = {"brand": "Cooplands", "brand_wikidata": "Q5167971"}
    start_urls = ["https://cooplands-bakery.co.uk/pages/our-shops"]

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        raw_json = response.xpath('//script[@type="application/json" and @data-locator-stores]/text()').get()
        if not raw_json:
            return

        for store in json.loads(raw_json):
            item = DictParser.parse(store)
            item["branch"] = item.pop("name", None)

            opening_hours = OpeningHours()
            for field, days in (
                ("weekdayHours", DAYS_WEEKDAY),
                ("saturdayHours", ["Sa"]),
                ("sundayHours", ["Su"]),
            ):
                if value := store.get(field):
                    if value.lower() == "closed":
                        opening_hours.set_closed(days)
                    elif ";" in value:
                        opening_hours.add_ranges_from_string(value)
                    else:
                        open_time, close_time = value.split("–")
                        opening_hours.add_days_range(days, open_time, close_time)

            if opening_hours:
                item["opening_hours"] = opening_hours

            apply_category(Categories.SHOP_BAKERY, item)
            yield item
