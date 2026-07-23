from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class FiveSarjTRSpider(Spider):
    name = "five_sarj_tr"
    item_attributes = {"brand": "5 Şarj", "brand_wikidata": "Q135753392"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest("https://5sarj.com/api/locations/map-pins")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["content"]:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["city"] = location["city"]["name"]
            apply_category(Categories.CHARGING_STATION, item)
            yield item
