from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsMYSpider(Spider):
    name = "mcdonalds_my"
    item_attributes = McdonaldsSpider.item_attributes

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://www.mcdonalds.com.my/storefinder/index.php",
            formdata={
                "action": "get_nearby_stores",
                "distance": "100000",
                "lat": "4",
                "lng": "101",
                "ajax": "1",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for index, store in enumerate(response.json()["stores"]):
            item = DictParser.parse(store)
            item["ref"] = index
            apply_category(Categories.FAST_FOOD, item)
            yield item
