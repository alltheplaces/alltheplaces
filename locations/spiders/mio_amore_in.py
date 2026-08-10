from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class MioAmoreINSpider(Spider):
    name = "mio_amore_in"
    item_attributes = {"brand": "Mio Amore", "brand_wikidata": "Q130534919"}
    start_urls = ["https://api.mioamoreshop.com/api/v2/store-management/get-store-locator-store"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["stores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("Mio Amore").strip(" -,")
            item["street_address"] = merge_address_lines([location["address_line_1"], location["address_line_2"]])
            item["postcode"] = location["pincode"]
            yield item
