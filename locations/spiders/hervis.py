from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class HervisSpider(Spider):
    name = "hervis"
    item_attributes = {"brand": "Hervis", "brand_wikidata": "Q1614816"}

    def start_requests(self):
        for country in ["at", "de", "hr", "hu", "ro", "si"]:
            url = f"https://www.hervis.{country}/api/v2/hervis-spa.{country}/stores?longitude=13.0417811&latitude=47.8007642&pageSize=500"
            yield JsonRequest(url=url)

    def parse(self, response, **kwargs):
        for store in response.json().get("stores"):
            item = DictParser.parse(store)
            item["ref"] = store.get("address").get("id")
            item["name"] = store.get("displayName")
            apply_category(Categories.SHOP_SPORTS, item)
            yield item
