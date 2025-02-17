import re
import time
import uuid
from typing import Any

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class PizzaHutVNSpider(scrapy.Spider):
    name = "pizza_hut_vn"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://pizzahut.vn/_next/static/chunks/700-ac6d47c5279a8d47.js"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        next_action_token = re.search(r"([a-f0-9]{40})", response.text).group(1)
        timestamp = int(time.time() * 1000)
        device_uid = uuid.uuid4()
        yield Request(
            url="https://pizzahut.vn/store-location?area=north",
            method="POST",
            body=f'[{{"url":"/store/GetAllStoreList","method":"get","bodyData":"","timeStamp":"{timestamp}","deviceUID":"{device_uid}"}}]',
            headers={
                "next-action": next_action_token,
            },
            callback=self.parse_token,
            meta=dict(timestamp=timestamp, device_uid=device_uid),
        )

    def parse_token(self, response: Response, **kwargs: Any) -> Any:
        access_token = re.search(r"1[:\s]+\"(.+)\"", response.text).group(1)
        yield JsonRequest(
            url="https://rwapi.pizzahut.vn/api/store/GetAllStoreList",
            headers={
                "Authorization": f"Bearer {access_token}",
                "deviceuid": str(response.meta["device_uid"]),
                "project_id": "WEB",
                "timestamp": str(response.meta["timestamp"]),
            },
            callback=self.parse_stores,
        )

    def parse_stores(self, response: Response, **kwargs: Any) -> Any:
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
