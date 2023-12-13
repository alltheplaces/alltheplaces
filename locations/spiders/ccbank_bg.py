from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_BG, OpeningHours


class ccbankBGSpider(Spider):
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
            if data["type"] == "3":
                apply_category(Categories.ATM, item)
            else:
                apply_category(Categories.BANK, item)

            yield item
