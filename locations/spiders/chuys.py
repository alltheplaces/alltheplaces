from typing import Any, AsyncIterator

import scrapy
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class ChuysSpider(scrapy.Spider):
    name = "chuys"
    item_attributes = {"brand": "Chuy's", "brand_wikidata": "Q5118415"}
    requires_proxy = True

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url="https://www.chuys.com/api/restaurants", headers={"x-source-channel": "WEB"})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["restaurants"]:
            location.update(location["contactDetail"].pop("address"))
            item = DictParser.parse(location)
            item["country"] = location["country"]
            item["name"] = location["restaurantName"]
            item["ref"] = location["restaurantNumber"]
            item["street_address"] = merge_address_lines([location.get("street2"), location.get("street1")])
            yield item
