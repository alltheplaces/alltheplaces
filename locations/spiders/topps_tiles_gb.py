from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class ToppsTilesGBSpider(Spider):
    name = "topps_tiles_gb"
    item_attributes = {"brand": "Topps Tiles", "brand_wikidata": "Q17026595"}
    requires_proxy = True

    def start_requests(self):
        yield JsonRequest(
            url="https://www.toppstiles.co.uk/api/locateStore",
            data={
                "address": "London",
                "country": "GB",
                "maxDistance": 1000,
                "limit": 500,
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["stores"]:
            store["street_address"] = store.pop("address")
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["country"] = store["country_id"]
            item["website"] = response.urljoin(store["url"])

            yield item
