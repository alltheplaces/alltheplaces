from copy import deepcopy
from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.items import Feature


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
            if store["dealer"].get("dealertype") == "V":  # sales & services both
                yield self.build_sales_item(item)
                yield self.build_service_item(item)
            elif store["dealer"].get("dealertype") == "S":  # services
                yield self.build_service_item(item)

    def build_sales_item(self, item: Feature) -> Feature:
        sales_item = deepcopy(item)
        sales_item["ref"] = f"{item['ref']}-SALES"
        apply_category(Categories.SHOP_CAR, sales_item)
        return sales_item

    def build_service_item(self, item: Feature) -> Feature:
        service_item = deepcopy(item)
        service_item["ref"] = f"{item['ref']}-SERVICE"
        apply_category(Categories.SHOP_CAR_REPAIR, service_item)
        return service_item
