import re

import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class StarbucksTHSpider(scrapy.Spider):
    name = "starbucks_th"
    item_attributes = {"brand": "Starbucks", "brand_wikidata": "Q37158"}
    start_urls = ["https://www.starbucks.co.th/find-a-store/"]

    def parse(self, response, **kwargs):
        data = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "places")]/text()').re_first(r"places\":(\[.+\]),\"styles")
        )
        for store in data:
            store.update(store.pop("location"))
            week_timing = [store["extra_fields"].get(day.lower(), "") for day in DAYS_FULL]
            if all("close" in timing.lower() for timing in week_timing):
                continue
            item = DictParser.parse(store)
            item["phone"] = store["extra_fields"]["tel"]
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if timing := store["extra_fields"].get(day.lower()):
                    if "24 hr" in timing.lower():
                        open_time, close_time = "00:00", "23:59"
                    elif m := re.match(r"(\d+:\d+)\s.+\s(\d+:\d+)", timing.replace(".", ":")):
                        open_time, close_time = m.groups()
                    else:
                        continue
                    item["opening_hours"].add_range(day, open_time, close_time)

            apply_category(Categories.COFFEE_SHOP, item)

            yield item
