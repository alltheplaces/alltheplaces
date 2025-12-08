import hashlib
import hmac
import time
from base64 import b64decode, b64encode
from typing import Any, AsyncIterator
from uuid import uuid4

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT


class PizzaHutVNSpider(Spider):
    name = "pizza_hut_vn"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    api_url = "https://rwapi.pizzahut.vn/api/store/GetAllStoreList"
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[JsonRequest]:
        timestamp = int(time.time() * 1000)
        device_uid = uuid4()

        auth_data = {"app_code": "REDWEB_DI1rpn3vHlyp", "access_key": "9GQ3cVW5Vqq4", "secret_key": "1YWkf7Rh0oJB"}

        query_string = f"TimeStamp={timestamp}&DeviceUID={device_uid}&AppCode={auth_data['app_code']}&AccessKey={auth_data['access_key']}&Method=GET&url=/STORE/GETALLSTORELIST&Body="

        key = b64decode(auth_data["secret_key"])
        message = query_string.encode("utf-8")
        signature = hmac.new(key, message, hashlib.sha512)

        access_token = b64encode(signature.digest()).decode("utf-8")

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
