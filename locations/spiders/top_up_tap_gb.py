import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class TopUpTapGBSpider(Spider):
    name = "top_up_tap_gb"
    item_attributes = {"operator": "Scottish Water", "operator_wikidata": "Q7438022"}
    start_urls = ["https://www.yourwateryourlife.co.uk/find-my-nearest-tap/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath('//*[@id="map-data"]/text()').get()):
            item = Feature()
            item["lat"] = location["position"]["lat"]
            item["lon"] = location["position"]["lng"]
            item["street_address"] = location["info"]["address"]
            item["city"] = location["info"]["city"]
            item["website"] = item["ref"] = location["info"]["url"]
            apply_category(Categories.DRINKING_WATER, item)
            yield item
