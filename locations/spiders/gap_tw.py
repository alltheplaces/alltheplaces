import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser


class GapTWSpider(scrapy.Spider):
    name = "gap_tw"
    item_attributes = {"brand": "Gap", "brand_wikidata": "Q420822", "extras": Categories.SHOP_CLOTHES.value}

    def start_requests(self):
        url = "https://api.gap.tw/store/queryStoreLocation"
        yield JsonRequest(
            url=url,
            method="POST",
            headers={"Content-Type": "application/json;charset=UTF-8"},
            data={"id": 1, "locationIdentifier": "Gap"},
        )

    def parse(self, response, **kwargs):
        for city in response.json()["data"][0]["cityList"]:
            for store in city["storeLocations"]:
                item = DictParser.parse(store)
                item["country"] = "TW"
                item["website"] = "https://www.gap.tw/"
                yield item
