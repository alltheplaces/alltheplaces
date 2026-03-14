from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class CarecoGBSpider(Spider):
    name = "careco_gb"
    item_attributes = {"name": "CareCo", "brand": "CareCo"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest("https://www.careco.co.uk/rest/default/V1/store-locator/showrooms")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            if isinstance(location["address2"], str):
                item["street_address"] = merge_address_lines([location["address1"], location["address2"]])

            apply_category(Categories.SHOP_MEDICAL_SUPPLY, item)

            yield item
