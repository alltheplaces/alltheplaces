from urllib.parse import urljoin

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class OrangeBESpider(scrapy.Spider):
    name = "orange_be"
    item_attributes = {"brand": "Orange", "brand_wikidata": "Q1431486"}
    start_urls = ["https://www.orange.be/nl/shop_locator/shop.json"]

    def parse(self, response):
        for store in response.json():
            if store["type"] in ["SHOP", "CENTER"]:
                item = DictParser.parse(store)
                item["street_address"] = store["address"]["thoroughfare"]
                item["website"] = item["extras"]["website:be"] = urljoin(
                    "https://www.orange.be/nl/shops/", store["slug"]
                )
                item["extras"]["website:fr"] = urljoin("https://www.orange.be/fr/shops/", store["slug"])
                item["opening_hours"] = self.parse_hours(store.get("opening_hours"))
                apply_category(Categories.SHOP_MOBILE_PHONE, item)
                yield item

    def parse_hours(self, hours):
        try:
            oh = OpeningHours()
            for rule in hours:
                oh.add_range(DAYS[int(rule["day"]) - 1], rule["starthours"], rule["endhours"], time_format="%H%M")
            return oh
        except:
            return None
