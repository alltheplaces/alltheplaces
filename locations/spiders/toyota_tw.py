import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ToyotaTWSpider(scrapy.Spider):
    name = "toyota_tw"
    item_attributes = {
        "brand": "Toyota",
        "brand_wikidata": "Q53268",
    }
    start_urls = ["https://www.toyota.com.tw/api/location.ashx"]

    def parse(self, response, **kwargs):
        for store in response.json()["DATA"]:
            item = DictParser.parse(store)
            item["website"] = "https://www.toyota.com.tw/"
            if store["TYPE"] == "1":
                item["ref"] = "-".join([store["KEY"], "Dealer"])
                apply_category(Categories.SHOP_CAR, item)
            elif store["TYPE"] == "2":
                item["ref"] = "-".join([store["KEY"], "Service"])
                apply_category(Categories.SHOP_CAR_REPAIR, item)

            yield item
