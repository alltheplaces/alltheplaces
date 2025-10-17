import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range, sanitise_day


class HoneyDewDonutsUSSpider(scrapy.Spider):
    name = "honey_dew_donuts_us"
    item_attributes = {"brand": "Honey Dew Donuts", "brand_wikidata": "Q5893524"}
    start_urls = ["https://honeydewdonuts.com/wp-json/acf/v3/business_locations?_embed&per_page=1000"]

    def parse(self, response, **kwargs):
        for result in response.json():
            if store := result.get("acf"):
                store.pop("region", "")
                item = DictParser.parse(store)
                item["street_address"] = ", ".join(
                    filter(None, [store.get("address_line_1"), store.get("address_line_2")])
                )
                item["phone"] = store.get("primary_phone")
                item["email"] = store.get("primary_email")
                if hours := store.get("hours"):
                    item["opening_hours"] = OpeningHours()
                    for rule in hours:
                        if m := re.match(r"(\w+)[\s-]*(\w+)?", rule.get("day")):
                            start_day = sanitise_day(m.group(1))
                            end_day = sanitise_day(m.group(2)) or start_day
                            if start_day:
                                item["opening_hours"].add_days_range(
                                    day_range(start_day, end_day), rule["start_time"], rule["end_time"], "%I:%M %p"
                                )
                apply_category(Categories.FAST_FOOD, item)
                yield item
