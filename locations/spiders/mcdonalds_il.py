from typing import AsyncIterator, Iterable

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class McdonaldsILSpider(JSONBlobSpider):
    name = "mcdonalds_il"
    item_attributes = {"brand_wikidata": "Q12061542"}
    start_urls = ["https://order.mcdonalds.co.il"]
    locations_key = ["data", "stores"]

    async def start(self) -> AsyncIterator[JsonRequest | Request]:
        yield scrapy.FormRequest(
            url="https://mapi.mcdonalds.co.il/api/website/9.3/setSettings",
            formdata={
                "lang_id": "1",
                "lang": "he",
                "resolution": "xxx",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "Origin": "https://order.mcdonalds.co.il",
                "Referer": "https://order.mcdonalds.co.il/",
            },
            method="POST",
            callback=self.parse_token,
        )

    def parse_token(self, response: TextResponse) -> Iterable[Feature]:
        token = response.json().get("data").get("auth_key")
        yield JsonRequest(
            url="https://mapi.mcdonalds.co.il/api/website/9.3/getStores",
            headers={"X-CSRF-TOKEN": token},
            method="POST",
            callback=self.parse_locations,
        )

    def parse_locations(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json().get("data").get("stores"):
            item = DictParser.parse(location)
            item["ref"] = location.get("StoreIndex")
            item["website"] = f"https://order.mcdonalds.co.il/restaurant/{item['ref']}"
            item["branch"] = location.get("StoreNameLong")
            yield item
