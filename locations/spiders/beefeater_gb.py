from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.spiders.vapestore_gb import clean_address


class BeefeaterGBSpider(Spider):
    name = "beefeater_gb"
    item_attributes = {"brand": "Beefeater", "brand_wikidata": "Q4879766"}
    start_urls = ["https://www.beefeater.co.uk/en-gb/locations.search.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["addr_full"] = clean_address(
                [
                    location["address1"],
                    location["address2"],
                    location["address3"],
                    location["address4"],
                    "United Kingdom",
                ]
            )
            item["website"] = response.urljoin(location["path"])
            item["phone"] = location["contactInfo"]

            yield item
