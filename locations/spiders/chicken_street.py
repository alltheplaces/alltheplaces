from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class ChickenStreetSpider(Spider):
    name = "chicken_street"
    item_attributes = {"brand": "Chicken Street", "brand_wikidata": "Q124669862"}
    start_urls = ["https://restaurants.chickenstreet.fr/wp-content/uploads/ssf-wp-uploads/ssf-data.json"]
    skip_auto_cc_domain = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["item"]:
            item = DictParser.parse(location)
            item["website"] = location["exturl"]

            yield item
