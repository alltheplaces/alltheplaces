import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class FujiserviceJPSpider(Spider):
    name = "fujiservice_jp"
    requires_proxy = True

    start_urls = ["https://fuji-service-cl.co.jp/wp-json/wpgmza/v1/features/"]
    allowed_domains = ["fuji-service-cl.co.jp"]
    country_code = "JP"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["markers"]:

            item = DictParser.parse(store)
            item["ref"] = re.search(r"^\S-\d{4}", str(store["title"])).group()
            item["extras"]["amenity"] = "luggage_locker"
            item["operator"] = "フジサービス"
            item["extras"]["operator:en"] = "Fuji Service"
            item["image"] = store["pic"]
            if "24時間" in store["description"]:
                item["opening_hours"] = "24/7"
            yield item
