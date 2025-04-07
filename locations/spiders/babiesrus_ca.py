from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class BabiesrusCASpider(Spider):
    name = "babiesrus_CA"
    item_attributes = {"brand": "Babies R Us", "brand_wikidata": "Q17232036"}
    start_urls = ["https://www.babiesrus.ca/en/stores-findstores?batch=100&showMap=false&radius=25000"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])

            yield item
