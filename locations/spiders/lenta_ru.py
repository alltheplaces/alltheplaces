import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class LentaRUSpider(scrapy.Spider):
    name = "lenta_ru"
    item_attributes = {"brand": "Лента", "brand_wikidata": "Q4258608"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    allowed_domains = ["lenta.com"]

    def start_requests(self):
        yield JsonRequest("https://lenta.com/api/v2/stores")

    def parse(self, response):
        for poi in response.json():
            item = DictParser.parse(poi)
            item["street_address"] = poi.get("address")
            item["addr_full"] = None
            self.parse_hours(item, poi)
            # A few stores are marked as pet shops
            if poi.get("type") == "zoo":
                apply_category(Categories.SHOP_PET, item)
            yield item

    def parse_hours(self, item, poi):
        if poi.get("is24hStore"):
            item["opening_hours"] = "24/7"
        else:
            oh = OpeningHours()
            oh.add_days_range(DAYS, poi.get("opensAt"), poi.get("closesAt"))
            item["opening_hours"] = oh.as_opening_hours()
