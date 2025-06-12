import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class AmericanGolfGBSpider(Spider):
    name = "american_golf_gb"
    item_attributes = {"brand": "American Golf", "brand_wikidata": "Q62657494"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = [
        "https://www.americangolf.co.uk/en/find-stores/",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(
            re.search(
                r"channel\":(\[.*\])}},\"content",
                response.xpath('//*[contains(text(),"address1")]/text()').get().replace("\\", ""),
            ).group(1)
        )
        for location in raw_data:
            location.update(location.pop("resources"))
            print(location)
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["addr_full"] = location["listAddress"]
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            yield item
