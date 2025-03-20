import chompjs
import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.bauhaus_nordics import BauhausNordicsSpider


class BauhausTRSpider(scrapy.Spider):
    name = "bauhaus_tr"
    item_attributes = BauhausNordicsSpider.item_attributes
    start_urls = ["https://www.bauhaus.com.tr/bauhaus-magazalari"]

    def parse(self, response):
        stores_city_list = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "storeList")]/text()').get()
        )
        for city_data in stores_city_list:
            for store_dict in city_data["stores"]:
                item = DictParser.parse(store_dict)
                item["opening_hours"] = self.parse_hours(store_dict)
                yield item

    def parse_hours(self, store_dict):
        oh = OpeningHours()
        for day in DAYS_FULL:
            if work_hr := store_dict.get("workinghours_" + day[0:3].lower()):
                start_hr, end_hr = work_hr.split("-")
                oh.add_range(day, start_hr, end_hr)
        return oh
