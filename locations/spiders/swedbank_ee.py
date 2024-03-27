import scrapy
import xmltodict

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class SwedbankEESpider(scrapy.Spider):
    name = "swedbank_ee"
    item_attributes = {"brand_wikidata": "Q1145493"}
    start_urls = ["https://www.swedbank.ee/finder.xml"]

    def parse(self, response):
        data = xmltodict.parse(response.text)
        for poi in data["items"]["item"]:
            item = DictParser.parse(poi)
            item["branch"] = item.pop("name")
            type = poi.get("type")
            if type in "ATM":
                apply_category(Categories.ATM, item)
            elif type == "R":
                apply_category(Categories.ATM, item)
                apply_yes_no(Extras.CASH_IN, item, True)
            elif type == "branch":
                apply_category(Categories.BANK, item)
            else:
                self.crawler.stats.inc_value(f"atp/unknown_type/{type}")
            yield item
