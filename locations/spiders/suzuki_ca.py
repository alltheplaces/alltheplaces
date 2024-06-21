import ast

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SuzukiCASpider(scrapy.Spider):
    name = "suzuki_ca"
    item_attributes = {"brand": "Suzuki", "brand_wikidata": "Q181642"}
    start_urls = [
        "https://www.suzuki.ca/wp-admin/admin-ajax.php?action=asl_load_stores&nonce=811ab7901d&load_all=1&layout=1"
    ]

    def parse(self, response, **kwargs):
        for dealer in response.json():
            item = DictParser.parse(dealer)
            item.pop("street", None)
            item["street_address"] = dealer["street"]
            item["opening_hours"] = OpeningHours()
            for day, time in ast.literal_eval(dealer.get("open_hours")).items():
                if time in ["0", 0, None]:
                    continue
                for open_close_time in time:
                    open_time, close_time = open_close_time.split("-")
                    item["opening_hours"].add_range(
                        day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I:%M %p"
                    )
            apply_category(Categories.SHOP_CAR, item)
            yield item
