import pprint
from urllib.parse import urljoin

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class StcSESpider(scrapy.Spider):
    name = "stc_se"
    item_attributes = {"brand": "STC", "brand_wikidata": "Q124061743"}
    start_urls = ["https://www.stc.se/assets/clubs.json"]

    def parse(self, response):
        for club in response.json():
            item = DictParser.parse(club)
            item["branch"] = item.pop("name")
            item["city"] = item["city"].title()
            item["street_address"] = item.pop("street")
            item["website"] = urljoin("https://www.stc.se/gym/", club["slug"])
            apply_yes_no(Extras.WIFI, item, "wifi" in club["includes"])

            item["opening_hours"] = OpeningHours()
            for rule in club["openingHours"]["default"]["data"]:
                pprint.pp(rule)
                if rule["hours"]["unmanned"] == "Dygnet runt":
                    start_time, end_time = "00:00", "23:59"
                else:
                    start_time, end_time = rule["hours"]["unmanned"].replace(" ", "").replace(".", ":").split("-")
                item["opening_hours"].add_range(rule["day"], start_time, end_time)
            apply_category(Categories.GYM, item)
            yield item
