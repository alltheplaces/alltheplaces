import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range


def wrap_add_range(oh: OpeningHours, day: str, rule: str, rules: {}):
    start_time = rules[rule + "_s"]
    end_time = rules[rule + "_e"]
    if start_time == "#N/A":
        return
    if start_time in ["00:00:00 AM", "0:00:00 AM"]:
        start_time = "12:00:00 AM"
    if end_time in ["00:00:00 PM", "0:0:00 PM", "0:00:00 PM"]:
        end_time = "12:00:00 PM"
    oh.add_range(day, start_time, end_time, time_format="%I:%M:%S %p")


CATEGORIES = {
    "CITY": ("Profi City", Categories.SHOP_SUPERMARKET),
    "LOCO": ("Profi Loco", Categories.SHOP_SUPERMARKET),
    "PROFI": ("Profi", Categories.SHOP_SUPERMARKET),
    "PROFI CITY": ("Profi City", Categories.SHOP_SUPERMARKET),
    "PROFI GO": ("Profi Go", Categories.SHOP_CONVENIENCE),
    "PROFI LOCO": ("Profi Loco", Categories.SHOP_SUPERMARKET),
    "PROFI MINI": ("Profi Mini", Categories.SHOP_CONVENIENCE),
    "PROFI SUPER": ("Profi Super", Categories.SHOP_SUPERMARKET),
}


class ProfiROSpider(scrapy.Spider):
    name = "profi_ro"
    item_attributes = {"brand": "Profi", "brand_wikidata": "Q956664"}
    start_urls = ["https://www.profi.ro/magazine/"]

    def parse(self, response):
        for store in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "STORE_LOCATIONS")]/text()').get()
        ):
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full")
            item["website"] = f'https://www.profi.ro/magazine/#{store["url"]}'
            try:
                oh = OpeningHours()
                for day in day_range("Mo", "Fr"):
                    wrap_add_range(oh, day, "open_mf", store)
                wrap_add_range(oh, "Sa", "open_sat", store)
                wrap_add_range(oh, "Su", "open_sun", store)
                item["opening_hours"] = oh
            except:
                pass

            item["name"], cat = CATEGORIES.get(store["type"]["name"], ("Profi", Categories.SHOP_SUPERMARKET))

            apply_category(cat, item)

            yield item
