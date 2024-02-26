from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.vapestore_gb import clean_address


class HootersSpider(scrapy.Spider):
    name = "hooters"
    item_attributes = {"brand": "Hooters", "brand_wikidata": "Q1025921"}
    allowed_domains = ["www.hooters.com"]
    start_urls = ["https://www.hooters.com/api/location_names.php"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            yield JsonRequest(
                url="https://www.hooters.com/api/set_my_location.php?id={}".format(location["id"]),
                callback=self.parse_location,
            )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        location = response.json()["location"]
        item = DictParser.parse(location)
        item["branch"] = item.pop("name")
        item["website"] = response.urljoin(location["detailsUrl"])
        item["street_address"] = location["address"]["line-1"]
        item["addr_full"] = clean_address([location["address"]["line-1"], location["address"]["line-2"]])

        item["opening_hours"] = OpeningHours()
        for day, times in (location["hours"] or {}).items():
            item["opening_hours"].add_range(
                day, times["open"], times["close"], "%H:%M" if len(times["open"]) == 5 else "%H:%M:%S"
            )

        yield item
