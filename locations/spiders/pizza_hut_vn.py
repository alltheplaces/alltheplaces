import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class PizzaHutVNSpider(scrapy.Spider):
    name = "pizza_hut_vn"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}

    def start_requests(self):
        yield JsonRequest(
            url="https://api2.pizzahut.vn/api-core/api/store/GetAllStoreList",
            headers={
                "Authorization": "Bearer T7RJyFN5ZY/2S7axVLhzLUd6SSBr8kVzvTwp4KdEk9qbcmQN1Zyz0F7fWQoRz6Jz7GjLA6TiFzmvdOhwCKkOCA==",
                "PROJECT_ID": "WEB",
            },
        )

    def parse(self, response, **kwargs):
        for store in response.json()["PZH_StoreList"]["StoreList"]:
            item = Feature()
            item["ref"] = store.get("store_code")
            item["lat"], item["lon"] = store.get("location", "").split(",")
            item["name"] = store.get("name_vi")
            item["extras"]["name:en"] = store.get("name_en")
            item["addr_full"] = store.get("add_vn")
            item["extras"]["addr:full:en"] = clean_address(store.get("add_en"))
            item["website"] = "https://pizzahut.vn/"
            if store.get("Open_Time") and store.get("Close_Time"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS, store["Open_Time"], store["Close_Time"])
            apply_category(Categories.RESTAURANT, item)
            yield item
