from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class ClintonsGBSpider(Spider):
    name = "clintons_gb"
    item_attributes = {"brand": "Clintons", "brand_wikidata": "Q5134299"}
    start_urls = ["https://clintonsretail.com/storeloc.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for feature in response.json()["features"]:
            item = Feature()
            item["geometry"] = feature["geometry"]
            item["geometry"]["type"] = "Point"  # spec needs title case
            item["ref"] = str(feature["properties"]["storeid"])
            item["addr_full"] = feature["properties"]["name"]
            item["phone"] = feature["properties"]["phone"]

            yield item
