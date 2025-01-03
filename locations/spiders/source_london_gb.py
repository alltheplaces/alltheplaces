from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SourceLondonGBSpider(Spider):
    name = "source_london_gb"
    item_attributes = {"brand": "Source London", "brand_wikidata": "Q7565133"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://www.sourcelondon.net/api/infra/location", headers={"X-API-VERSION": "2"}, callback=self.parse
        )

    def parse(self, response, **kwargs):
        for location in response.json()["internalLocations"]:
            item = DictParser.parse(location)
            apply_category(Categories.CHARGING_STATION, item)
            yield item
