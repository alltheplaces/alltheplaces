from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_AT, OpeningHours


class A1ATSpider(Spider):
    name = "a1_at"
    item_attributes = {"brand": "A1", "brand_wikidata": "Q688755"}
    allowed_domains = ["www.a1.net"]
    start_urls = ["https://www.a1.net/o/gucci/widgets/apis/shopfinder/bff/microservice-shopfinder/shop/basicData"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_store_list)

    def parse_store_list(self, response):
        for location in response.json():
            if location["type"] != "SHOP":
                # DEALER, IT_PARTNER, POST, EXCLUSIVE_STORE
                # and PREFERRED_PARTNER should be ignored.
                continue
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full", None)
            yield JsonRequest(
                url=f'https://www.a1.net/o/gucci/widgets/apis/shopfinder/bff/microservice-shopfinder/shop/detail/id/{item["ref"]}',
                meta={"item": item},
                callback=self.parse_store,
            )

    def parse_store(self, response):
        item = response.meta["item"]
        location = response.json()["basicShopData"]
        item["phone"] = location.get("phone")
        item["email"] = location.get("email")
        item["website"] = location.get("url")
        item["opening_hours"] = OpeningHours()
        for day_hours in response.json().get("hoursShops", []):
            item["opening_hours"].add_range(
                DAYS_AT[day_hours["days"]], day_hours["tsFrom"], day_hours["tsTo"], "%H%M%S"
            )
        yield item
