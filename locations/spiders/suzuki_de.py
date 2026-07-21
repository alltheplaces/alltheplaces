from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations


class SuzukiDESpider(Spider):
    name = "suzuki_de"
    item_attributes = {"brand": "Suzuki", "brand_wikidata": "Q181642"}

    async def start(self) -> AsyncIterator[Request]:
        for city in city_locations("DE", 50000):
            params = {
                "dealertype": ["V", "S"],
                "searchtype": "2",
                "count": "20",
                "radius": "50",
                "lat": str(city["latitude"]),
                "lng": str(city["longitude"]),
            }
            yield Request(url="https://auto.suzuki.de/dealersearch/search?" + urlencode(params, doseq=True))

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            store["location"]["name"] = store["dealer"].get("dealername")
            store["location"]["website"] = store["dealer"].get("homepage")
            store["location"]["province"] = store["dealer"].get("province")
            item = DictParser.parse(store["location"])
            apply_category(Categories.SHOP_CAR, item)
            yield item
