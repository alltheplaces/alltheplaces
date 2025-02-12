from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class CakeBoxGBSpider(Spider):
    name = "cake_box_gb"
    item_attributes = {"brand": "Cake Box", "brand_wikidata": "Q110057905"}
    start_urls = ["https://api.cakebox.com/sf/store/store-locations/search?limit=0&offset=0"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["facebook"] = location.get("facebook_link")
            item["street_address"] = location["address"]["address_1"]
            yield item
