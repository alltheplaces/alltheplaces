import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_BG, OpeningHours
from locations.items import Feature


class A1BGSpider(scrapy.Spider):
    name = "a1_bg"
    item_attributes = {"brand": "A1", "brand_wikidata": "Q1941592", "country": "BG"}
    allowed_domains = ["www.a1.bg"]
    start_urls = ["https://www.a1.bg/1/mm/shops/mc/index/ma/index/mo/1?ajaxaction=getShopsWithWorkTime"]

    def parse(self, response):
        for store in response.json()["response"]:
            item = DictParser.parse(store)
            item["street_address"] = store["address"].strip()
            item["opening_hours"] = self.get_opening_hours(store)
            yield Feature(item)

    def get_opening_hours(self, store):
        oh = OpeningHours()
        for rule in store["worktime"]:
            rule_str = f"{rule['workday']} {rule['hour_from']}-{rule['hour_to']}"
            oh.add_ranges_from_string(rule_str, DAYS_BG)

        return oh.as_opening_hours()
