import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class WilliamPennINSpider(Spider):
    name = "william_penn_in"
    item_attributes = {"brand": "William Penn", "brand_wikidata": "Q122439152"}
    allowed_domains = ["engine.kartmax.in"]

    def start_requests(self):
        headers = {"Origin": "https://www.williampenn.net"}
        yield JsonRequest(url="https://engine.kartmax.in/api/cart/v1/store-locator/list?site=null", headers=headers)

    def parse(self, response):
        for location in response.json()["data"]:
            if not location.get("is_active"):
                continue
            item = DictParser.parse(location)
            item["addr_full"] = re.sub(r"\s+", " ", item.get("addr_full", ""))
            item["postcode"] = location["pincode"]
            apply_category(Categories.SHOP_STATIONERY, item)
            yield item
