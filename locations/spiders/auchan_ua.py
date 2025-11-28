from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class AuchanUASpider(Spider):
    name = "auchan_ua"
    item_attributes = {"brand_wikidata": "Q4073419"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        url = "https://auchan.ua/graphql/?query=query%20getWarehouses%20%7B%0A%20getAuchanWarehouses%20%7B%0A%20warehouses%20%7B%0A%20code%0A%20city%0A%20city_ru%0A%20hours%0A%20address%0A%20title%0A%20position%20%7B%0A%20latitude%0A%20longitude%0A%20__typename%0A%20%7D%0A%20__typename%0A%20%7D%0A%20__typename%0A%20%7D%0A%7D%0A&operationName=getWarehouses"
        yield JsonRequest(url=url, callback=self.parse)

    def parse(self, response, **kwargs):
        for store in response.json()["data"]["getAuchanWarehouses"]["warehouses"]:
            store.update(store.pop("position"))
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full")
            item["city"] = store["city_ru"]
            item["ref"] = store["code"]
            item["opening_hours"] = OpeningHours()
            if store["hours"] not in ["Зачинено", "Зачинений"]:
                open_time, close_time = store["hours"].split("-")
                for day in DAYS:
                    item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
