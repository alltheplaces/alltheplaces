import base64
import hashlib
import hmac
import re
import time
import uuid
from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class PizzaHutVNSpider(scrapy.Spider):
    name = "pizza_hut_vn"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://pizzahut.vn/_next/static/chunks/3070-0d2156c9136abbb1.js"]
    api_url = "https://rwapi.pizzahut.vn/api/store/GetAllStoreList"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        timestamp = int(time.time() * 1000)
        device_uid = uuid.uuid4()

        app_code, secret_key, access_key = re.findall(
            r"[a-z][\s=]+\(0,[\n\s]*[a-z]\.[a-z]\)\(\"([a-z0-9]+)\"\)", response.text
        )[:3]

        query_string = f"TimeStamp={timestamp}&DeviceUID={device_uid}&AppCode={app_code}&AccessKey={access_key}&Method=GET&url={self.api_url}&Body="

        key = base64.b64decode(secret_key)
        message = query_string.encode("utf-8")
        signature = hmac.new(key, message, hashlib.sha512)

        access_token = base64.b64encode(signature.digest()).decode("utf-8")

        yield JsonRequest(
            url=self.api_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "deviceuid": str(device_uid),
                "project_id": "WEB",
                "timestamp": str(timestamp),
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
