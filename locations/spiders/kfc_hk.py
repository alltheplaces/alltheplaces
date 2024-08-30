from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.items import Feature
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcHKSpider(scrapy.Spider):
    name = "kfc_hk"
    item_attributes = KFC_SHARED_ATTRIBUTES

    def start_requests(self):
        yield JsonRequest(
            url="https://ordering.kfchk.com/Action",
            data={
                "actionName": "candao.storeStandard.getStoreList",
                "langType": 2,
                "content": {
                    "businessType": ["3"],
                    "searchName": "",
                    "pageNow": 1,
                    "pageSize": 150,
                    "filterUnnecessaryQuery": True,
                    "mapSystemSort": 1,
                    "crmCode": "azure",
                    "brand": "KFCHK",
                    "source": "Web",
                    "language": "E",
                },
            },
            callback=self.parse,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]["rows"]:
            item = Feature()
            item["branch"] = store["storeNameTw"]
            item["city"] = store["districtName"]
            item["phone"] = store["customerHotline"]
            item["addr_full"] = store["storeAddress"]
            item["geometry"] = store["coordinate"]
            item["ref"] = store["storeId"]
            item["website"] = "https://www.kfchk.com/"
            yield item
