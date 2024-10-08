from scrapy import Spider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_BG, OpeningHours


class CcbankBGSpider(Spider):
    name = "ccbank_bg"
    item_attributes = {"brand": "Central Cooperative Bank", "brand_wikidata": "Q2944755"}
    allowed_domains = ["ccbank.bg"]
    start_urls = ["https://ccbank.bg/bg/branches_network/offices"]

    def parse(self, response):
        for data in response.json()["data"]:
            item = DictParser.parse(data)

            item["opening_hours"] = OpeningHours()
            if data["workhours"]:
                item["opening_hours"].add_ranges_from_string(data["workhours"].replace(" - ", ","), days=DAYS_BG)
            if data["type"] == "3" or data["type"] == "4":
                apply_category(Categories.ATM, item)
                apply_yes_no(
                    "cash_in", item, data["type"] == "4", False
                )  # ATMs of type 4 have deposit functionality, type 3 don't have it
            else:
                apply_category(Categories.BANK, item)

            yield item
