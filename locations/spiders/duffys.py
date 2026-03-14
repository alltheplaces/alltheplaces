from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class DuffysSpider(Spider):
    name = "duffys"
    item_attributes = {"name": "Duffy's", "brand": "Duffy's"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://api.duffysmvp.com/api/app/nearByLocations",
            data={"latitude": "26.6289791", "longitude": "-80.0724384"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["facebook"] = "https://www.facebook.com/{}".format(item["facebook"])
            item["ref"] = store["code"]

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "american"

            yield item
