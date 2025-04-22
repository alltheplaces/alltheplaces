from typing import Any, Iterable

from scrapy.http import JsonRequest, Request, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.geo import city_locations


class ZaxbysUSSpider(Spider):
    name = "zaxbys_us"
    item_attributes = {"brand": "Zaxby's", "brand_wikidata": "Q8067525"}

    def start_requests(self) -> Iterable[Request]:
        for city in city_locations("US", 15000):
            yield JsonRequest(
                url=f'https://zapi.zaxbys.com/v1/stores/near?latitude={city["latitude"]}&longitude={city["longitude"]}&radius=300',
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full", None)
            yield item
