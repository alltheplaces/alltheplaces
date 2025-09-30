import scrapy
import scrapy.http

from locations.dict_parser import DictParser
from locations.hours import DAYS_TR, OpeningHours, sanitise_day


class GratisTRSpider(scrapy.Spider):
    name = "gratis_tr"
    start_urls = [
        "https://api.gratis.retter.io/1oakekr4e/CALL/StoreManager/getStores/default?__culture=tr_TR&__platform=WEB"
    ]
    item_attributes = {"brand": "Gratis", "brand_wikidata": "Q28605813"}

    def parse(self, response):
        for store in response.json()["storeList"]:
            item = DictParser.parse(store)
            item["addr_full"] = store["addressText"]
            oh = OpeningHours()
            for day_time in store["workingHours"]:
                day = sanitise_day(day_time["day"], DAYS_TR)
                open_time, close_time = day_time["hours"].split(" - ")
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
            item["opening_hours"] = oh
            yield item
