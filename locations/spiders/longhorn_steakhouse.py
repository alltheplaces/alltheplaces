from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class LonghornSteakhouseSpider(Spider):
    name = "longhorn_steakhouse"
    item_attributes = {"brand": "LongHorn Steakhouse", "brand_wikidata": "Q3259007"}

    def start_requests(self):
        url = "https://m.longhornsteakhouse.com/api/restaurants?"
        yield JsonRequest(url=url, headers={"X-Source-Channel": "WEB"})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["restaurants"]:
            location.update(location.pop("contactDetail"))
            item = DictParser.parse(location)
            item["ref"] = location["restaurantNumber"]
            item["branch"] = location["restaurantName"]
            item["phone"] = location["phoneDetail"][0].get("phoneNumber")
            item["street_address"] = location["address"].get("street1")
            item["lat"] = location["address"]["coordinates"]["latitude"]
            item["lon"] = location["address"]["coordinates"]["longitude"]

            yield item
