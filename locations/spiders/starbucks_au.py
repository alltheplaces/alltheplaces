import html
import re

import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day


class StarbucksAUSpider(scrapy.Spider):
    name = "starbucks_au"
    item_attributes = {"brand": "Starbucks", "brand_wikidata": "Q37158"}
    start_urls = ["https://www.starbucks.com.au/find-a-store/"]

    def parse(self, response, **kwargs):
        stores = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "features")]/text()').re_first(r"let features = (.+);")
        )
        for store in stores["features"]:
            if "closed" in store["properties"].get("address", ""):
                continue
            item = DictParser.parse(store["properties"])
            item["website"] = store["properties"].get("store_link")

            if timing := store["properties"].get("openhours"):
                item["opening_hours"] = OpeningHours()
                for day, start_time, start_am_pm, end_time, end_am_pm in re.findall(
                    r"(\w+)<.+?>\s*(\d+[.:\d]*)\s*(am|pm)?.+?(\d+[.:\d]*)\s*(am|pm)?", html.unescape(timing)
                ):
                    try:
                        if day := sanitise_day(day):
                            open_time, close_time = [
                                t + ":00" if ":" not in t else t
                                for t in [start_time.replace(".", ":"), end_time.replace(".", ":")]
                            ]
                            time_format = "%H:%M"
                            if start_am_pm and end_am_pm:
                                open_time = f"{open_time} {start_am_pm}"
                                close_time = f"{close_time} {end_am_pm}"
                                time_format = "%I:%M %p"
                            item["opening_hours"].add_range(day, open_time, close_time, time_format=time_format)
                    except:
                        pass

            apply_category(Categories.COFFEE_SHOP, item)
            yield item
