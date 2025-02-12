import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES


class StarbucksBRSpider(scrapy.Spider):
    name = "starbucks_br"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES
    start_urls = ["https://starbucks.com.br/lojas"]
    requires_proxy = True

    def parse(self, response, **kwargs):
        details = chompjs.parse_js_object(response.xpath('//script[contains(text(), "var placesList")]/text()').get())
        for store in details:
            store["address"]["street_address"] = store["address"].pop("street")
            item = DictParser.parse(store)
            item["ref"] = store.pop("idPlace")
            item["website"] = response.url
            oh = OpeningHours()
            for rule in store["openingHours"]["weekdays"]:
                if not rule["isOpen"]:
                    continue
                day = sanitise_day(rule["name"])
                if not day:
                    continue
                for period in range(1, 2):  # iterate only once,since second shift has weird data
                    start_time = rule.get(f"hourStart{period}")
                    end_time = rule.get(f"hourEnd{period}")
                    if start_time and end_time:
                        oh.add_range(day, start_time, end_time, "%H:%M:%S")
            item["opening_hours"] = oh
            apply_category(Categories.COFFEE_SHOP, item)
            yield item
