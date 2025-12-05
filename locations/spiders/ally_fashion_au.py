from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class AllyFashionAUSpider(Spider):
    name = "ally_fashion_au"
    item_attributes = {"brand": "Ally Fashion", "brand_wikidata": "Q19870623"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://allyfashion.com/apps/storelocator/locator/get/active?perPage=999")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([item["street_address"], store.get("address2")])
            yield item
