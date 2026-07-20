from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Response, JsonRequest

from locations.categories import apply_category, Categories
from locations.dict_parser import DictParser


class FiveSarjTRSpider(Spider):
    name = "five_sarj_tr"
    item_attributes = {"brand": "5 Şarj", "brand_wikidata": "Q135753392"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest("https://5sarj.com/api/locations/map-pins")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["content"]:
            item = DictParser.parse(location)
            item["city"] = location["city"]["name"]
            apply_category(Categories.CHARGING_STATION, item)
            yield item
