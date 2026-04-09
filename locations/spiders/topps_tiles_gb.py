from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class ToppsTilesGBSpider(Spider):
    name = "topps_tiles_gb"
    item_attributes = {"brand": "Topps Tiles", "brand_wikidata": "Q17026595"}
    start_urls = ["https://www.toppstiles.co.uk/api/n/find?type=store"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["catalog"]:
            store["street_address"] = store.pop("address")
            if isinstance(store.get("postcode"), int):
                store.pop("postcode")
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["country"] = store["country_id"]
            item["website"] = response.urljoin(store["url"])

            yield item
