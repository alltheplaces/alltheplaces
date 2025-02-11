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
        # Token is generated using a timestamp and other parameters, but the timestamp-token pair remains consistent.
        # Skipping complex JavaScript token generation implementation.
        yield JsonRequest(
            url="https://rwapi.pizzahut.vn/api/store/GetAllStoreList",
            headers={
                "Authorization": "Bearer 5EGv68487qV+zXxlX73CFsL8L8PPBmzKEoI9AzHvrvVm95T4KpV/Ggu9zyruZvkHLFwc69R+tqoOnP5epRXRWQ==",
                "deviceuid": "47dcdf29-8d34-4beb-ac1f-8b91537cea35",
                "project_id": "WEB",
                "timestamp": "1739260740720",
            },
        )

    def parse(self, response, **kwargs):
        for store in response.json()["PZH_StoreList"]["StoreList"]:
            item = Feature()
            item["ref"] = store.get("store_code")
            item["lat"], item["lon"] = store.get("location", "").split(",")
            item["branch"] = store.get("name_vi").removeprefix("Pizza Hut ")
            item["extras"]["branch:en"] = store.get("name_en").removeprefix("Pizza Hut ")
            item["addr_full"] = store.get("add_vn")
            item["extras"]["addr:full:en"] = clean_address(store.get("add_en"))
            if store.get("Open_Time") and store.get("Close_Time"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS, store["Open_Time"], store["Close_Time"])
            apply_category(Categories.RESTAURANT, item)
            yield item
