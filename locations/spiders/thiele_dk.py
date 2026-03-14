import json

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_DK, OpeningHours


class ThieleDKSpider(scrapy.Spider):
    name = "thiele_dk"
    item_attributes = {"brand": "Thiele", "brand_wikidata": "Q12339176"}
    start_urls = [
        "https://www.thiele.dk/find-butik/",
    ]

    def parse(self, response, **kwargs):
        for store in json.loads(response.xpath("//@data-butiks").get()):
            item = DictParser.parse(store)
            item["email"] = None
            apply_category(Categories.SHOP_OPTICIAN, item)
            item["street_address"] = item.pop("addr_full", None)
            item["website"] = item["ref"] = "https://www.thiele.dk/butikker/" + item["name"].lower().replace(" ", "-")
            oh = OpeningHours()
            for day_time in store["schedule"]:
                oh.add_ranges_from_string(day_time["time"], DAYS_DK)
            item["opening_hours"] = oh
            yield item
