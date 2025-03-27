import re

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day


class SparDESpider(scrapy.Spider):
    name = "spar_de"
    item_attributes = {"brand": "Spar", "brand_wikidata": "Q610492"}

    def start_requests(self):
        for lat, lon in [
            (48.65141, 12.23430),
            (48.56922, 9.16833),
            (50.01477, 8.13253),
            (50.25378, 11.26065),
            (51.65005, 13.31153),
            (51.02888, 7.73892),
            (53.17877, 12.77292),
            (53.10421, 9.83124),
            (52.13586, 8.67114),
        ]:
            yield JsonRequest(
                url=f"https://spar-express.de/wp-admin/admin-ajax.php?action=store_search&lat={lat}=&lng={lon}&max_results=100&search_radius=165",
            )

    def parse(self, response, **kwargs):
        for shop in response.json():
            shop["street_address"] = ", ".join(filter(None, [shop.pop("address"), shop.pop("address2")]))
            item = DictParser.parse(shop)
            item["opening_hours"] = OpeningHours()
            timing = shop.get("hours")
            for day, open_time, close_time in re.findall(r">\s*(\w+)[<>\w\s/]*(\d\d:\d\d)\s*-\s*(\d\d:\d\d)", timing):
                if day := sanitise_day(day):
                    item["opening_hours"].add_range(day, open_time, close_time)
            apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
