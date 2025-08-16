from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class FujiserviceJPSpider(Spider):
    name = "fujiservice_jp"

    start_urls = ["https://fuji-service-cl.co.jp/wp-json/wpgmza/v1/features/"]
    allowed_domains = ["fuji-service-cl.co.jp"]
    country_code = "JP"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["markers"]:

            item = DictParser.parse(store)
            item["ref"] = store["id"]
            item["extras"]["amenity"] = "luggage_locker"
            item["operator"] = "フジサービス"
            item["extras"]["operator:en"] = "Fuji Service"
            item["image"] = store["pic"]
            yield item
