from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.pipelines.address_clean_up import merge_address_lines


class PepeJeansINSpider(Spider):
    name = "pepe_jeans_in"
    item_attributes = {"brand": "Pepe Jeans", "brand_wikidata": "Q426992"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Any]:
        for city in city_locations("IN", 100000):
            yield JsonRequest(
                url=f"https://www.pepejeans.in/on/demandware.store/Sites-MIRAI-Site/default/Stores-FindStores?radius=4000.0&postalCode={city['name']}"
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if data := response.json().get("stores"):
            for location in data:
                item = DictParser.parse(location)
                item["branch"] = item.pop("name").replace("Pepe Jeans - ", "")
                item["addr_full"] = merge_address_lines([item.pop("street_address"), location["address2"]])

                apply_category(Categories.SHOP_CLOTHES, item)

                yield item
