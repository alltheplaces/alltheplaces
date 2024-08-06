import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class AuchanUASpider(scrapy.Spider):
    name = "auchan_ua"
    item_attributes = {"brand": "Auchan", "brand_wikidata": "Q4073419", "extras": Categories.SHOP_SUPERMARKET.value}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        url = "https://auchan.ua/graphql/?query=query%20getWarehouses%20%7B%0A%20getAuchanWarehouses%20%7B%0A%20warehouses%20%7B%0A%20code%0A%20city%0A%20city_ru%0A%20hours%0A%20address%0A%20title%0A%20position%20%7B%0A%20latitude%0A%20longitude%0A%20__typename%0A%20%7D%0A%20__typename%0A%20%7D%0A%20__typename%0A%20%7D%0A%7D%0A&operationName=getWarehouses"
        yield JsonRequest(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        for store in response.json()["data"]["getAuchanWarehouses"]["warehouses"]:
            store.update(store.pop("position"))
            item = DictParser.parse(store)
            item["city"] = store["city_ru"]
            item["ref"] = store["code"]
            item["website"] = "https://auchan.ua/"
            item["opening_hours"] = OpeningHours()
            if store["hours"] not in ["Зачинено", "Зачинений"]:
                open_time, close_time = store["hours"].split("-")
                for day in DAYS:
                    item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())

            yield item
