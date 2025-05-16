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
from locations.user_agents import BROWSER_DEFAULT


class PizzaHutVNSpider(scrapy.Spider):
    name = "pizza_hut_vn"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://pizzahut.vn/store-location?area=north"]
    api_url = "https://rwapi.pizzahut.vn/api/store/GetAllStoreList"
    user_agent = BROWSER_DEFAULT

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Search for the desired JavaScript file
        yield response.follow(
            url=response.xpath("//script/@src").re(r"/_next/static/chunks/3070-\w+\.js")[-1],
            callback=self.parse_auth_token,
        )

    def parse_auth_token(self, response: Response, **kwargs: Any) -> Any:
        timestamp = int(time.time() * 1000)
        device_uid = uuid.uuid4()

        auth_data = {}
        for auth_param in ["app_code", "access_key", "secret_key"]:
            if identifier := self.find_identifier(response, auth_param.title().replace("_", "")):
                pattern = re.compile(rf"{identifier}[\s=]+\(0,[\n\s]*[a-z]\.[a-z]\)\(\"([a-z0-9]+)\"\)")
            else:  # secret_key
                pattern = re.compile(r"s[\s=]+\(0,[\n\s]*[a-z]\.[a-z]\)\(\"([a-z0-9]+)\"\)")

            auth_data[auth_param] = re.search(pattern, response.text).group(1)

        query_string = f"TimeStamp={timestamp}&DeviceUID={device_uid}&AppCode={auth_data['app_code']}&AccessKey={auth_data['access_key']}&Method=GET&url={self.api_url}&Body="

        key = base64.b64decode(auth_data["secret_key"])
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

    def find_identifier(self, response: Response, key: str) -> str | None:
        pattern = re.compile(rf"\"&{key}=\"\)\.concat\(([a-z]),")
        if match := re.search(pattern, response.text):
            return match.group(1)
        else:
            return None
