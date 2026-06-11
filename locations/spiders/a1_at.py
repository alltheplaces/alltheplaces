from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_AT, OpeningHours
from locations.items import Feature


class A1ATSpider(Spider):
    name = "a1_at"
    item_attributes = {"brand": "A1", "brand_wikidata": "Q688755"}
    requires_proxy = True
    allowed_domains = ["www.a1.net"]
    start_urls = ["https://www.a1.net/o/gucci/widgets/apis/shopfinder/bff/microservice-shopfinder/shop/basicData"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_store_list)

    def parse_store_list(self, response: Response) -> Iterable[JsonRequest]:
        for location in response.json():
            if location["type"] != "SHOP":
                # Only SHOP is an A1 corporate store. Other types
                # (DEALER, IT_PARTNER, EXCLUSIVE_STORE, EXCLUSIVE_PARTNER,
                # PREFERRED_PARTNER, ...) are independent partners.
                continue
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full", None)
            item["branch"] = item.pop("name").replace("A1 Shop ", "").strip()
            yield JsonRequest(
                url=f'https://www.a1.net/o/gucci/widgets/apis/shopfinder/bff/microservice-shopfinder/shop/detail/id/{item["ref"]}',
                meta={"item": item},
                callback=self.parse_store,
            )

    def parse_store(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["opening_hours"] = OpeningHours()
        for day_hours in response.json().get("hoursShops", []):
            item["opening_hours"].add_range(
                DAYS_AT[day_hours["days"]], day_hours["tsFrom"], day_hours["tsTo"], "%H%M%S"
            )
        yield item
