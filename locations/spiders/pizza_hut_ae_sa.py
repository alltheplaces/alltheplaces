import uuid
from typing import Any, Iterable

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class PizzaHutAESASpider(scrapy.Spider):
    name = "pizza_hut_ae_sa"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = True
    user_agent = BROWSER_DEFAULT

    def start_requests(self) -> Iterable[JsonRequest]:
        for key, value in {"uae": "uae", "saudi": "ksa"}.items():
            body = f'{{"payload":{{"path":"https://phprodblob-a0gebddqcze0bwhz.a03.azurefd.net/phprodblobstorage/phd/production/","country":"{value}","subPath":"?sv=2020-02-10&ss=bf&srt=o&sp=rlf&se=2025-06-21T02:09:06Z&st=2021-06-20T18:09:06Z&spr=https&sig=1jVlax0%2FNb2czQlUGw6kZv5KEvtVHSu4T7F0s0%2Fefyw%3D"}}}}'
            headers = {
                "brand": "PHD",
                "country": value.upper(),
                "deviceid": str(uuid.uuid4()),
            }
            url = f"https://{key}.pizzahut.me/api/getStoreList"
            yield JsonRequest(url=url, method="POST", body=body, headers=headers, cb_kwargs={"country": key})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for data in response.json()["data"]:
            for store in data["store"]:
                item = DictParser.parse(store)
                item["name"] = store.get("name_en")
                item["addr_full"] = store.get("address_en")
                item["street_address"] = store.get("areaName")
                item["phone"] = store.get("phone1")
                item["website"] = f"https://{kwargs['country']}.pizzahut.me/"
                if kwargs["country"] == "uae":
                    item["country"] = "AE"
                elif kwargs["country"] == "saudi":
                    item["country"] = "SA"
                apply_category(Categories.RESTAURANT, item)
                yield item
