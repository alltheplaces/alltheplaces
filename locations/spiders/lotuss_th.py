import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class LotussTHSpider(scrapy.Spider):
    name = "lotuss_th"
    start_urls = ["https://corporate.lotuss.com/location/json-data/"]
    LOTUSS = ("Lotus's", "Q2378901")
    LOTUSS_GO_FRESH = ("Lotus's go fresh", "Q125937967")

    def parse(self, response):
        store_list = response.json()["data"]
        for store in store_list:
            item = DictParser.parse(store)
            item["name"] = item.get("name", "").replace("\n", " ")
            item["extras"]["name:th"] = item["name"]
            item["website"] = "https://corporate.lotuss.com/"
            item["opening_hours"] = self.parse_hours(store["opening_hours"])

            match store["type"]:
                case "stores-lotuss-express":
                    item["brand"], item["brand_wikidata"] = self.LOTUSS_GO_FRESH
                    apply_category(Categories.SHOP_CONVENIENCE, item)
                case "stores-lotuss-extra" | "stores-lotuss-market":
                    if "Go Fresh" in store["name"] or "โก เฟรช" in store["name"]:
                        item["brand"], item["brand_wikidata"] = self.LOTUSS_GO_FRESH
                    else:
                        item["brand"], item["brand_wikidata"] = self.LOTUSS
                    apply_category(Categories.SHOP_SUPERMARKET, item)
                case _:
                    self.logger.error(f"Unknown store type: {store['type']}")
            yield item

    def parse_hours(self, op_hr_str):
        if op_hr_str:
            if "24 ชม" in op_hr_str:
                return "24/7"
            else:
                day_hr = re.search(r"(\d{1,2}:\d{1,2})\s*.\s*(\d{1,2}:\d{1,2})", op_hr_str, re.DOTALL)
                if day_hr:
                    start_hr, end_hr = day_hr.group(1), day_hr.group(2)
                    oh = OpeningHours()
                    for day in DAYS:
                        oh.add_range(day, start_hr, end_hr)
                    return oh
