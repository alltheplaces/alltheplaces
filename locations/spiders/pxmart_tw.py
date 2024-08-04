from typing import Iterable

import scrapy
from scrapy.http import JsonRequest, Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class PxmartTWSpider(scrapy.Spider):
    name = "pxmart_tw"
    item_attributes = {"brand_wikidata": "Q7262792"}
    start_urls = ["https://www.pxmart.com.tw/customer-service/stores"]

    def parse(self, response) -> Iterable[Request]:
        cities = response.xpath('//select[@name="city"]/option/@value').getall()
        for city in cities:
            payload = {"city": city, "area": "", "street": "", "name": "", "services": []}
            yield JsonRequest("https://www.pxmart.com.tw/api/stores", data=payload, callback=self.parse_pois)

    def parse_pois(self, response):
        for poi in response.json()["data"]:
            poi = dict(poi, **poi.get("attributes", {}))
            item = DictParser.parse(poi)

            oh = OpeningHours()
            oh.add_days_range(DAYS, poi.get("startDate"), poi.get("endDate"))
            item["opening_hours"] = oh

            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
