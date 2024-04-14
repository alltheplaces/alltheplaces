from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class TableTableGBSpider(Spider):
    name = "table_table_gb"
    item_attributes = {"brand": "Table Table", "brand_wikidata": "Q16952586"}
    start_urls = ["https://www.tabletable.co.uk/en-gb/locations.search.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = None
            item["addr_full"] = merge_address_lines(
                [
                    location["address1"],
                    location["address2"],
                    location["address3"],
                    location["address4"],
                ]
            )
            item["website"] = response.urljoin(location["path"])
            item["phone"] = location["contactInfo"]

            yield item
