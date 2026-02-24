from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class MetaLocatorSpider(Spider):
    """
    API documentation available at:
    https://admin.metalocator.com/components/com_locator/assets/documents/api/classes/LocatorControllerAPI.html#method_search

    To use this spider, specify a `brand_id` attribute, which corresponds to
    the `Itemid` query attribute in API request URLs that may be observed on
    storefinder pages.
    """

    dataset_attributes: dict = {"source": "api", "api": "metalocator.com"}
    allowed_domains: list[str] = ["code.metalocator.com"]
    brand_id: str
    custom_settings: dict = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=f"https://code.metalocator.com/webapi/api/search/?Itemid={self.brand_id}&limit=100000")

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json():
            item = DictParser.parse(location)
            item.pop("addr_full")
            item["street_address"] = ", ".join(filter(None, [location["address"], location["address2"]]))
            if location.get("hours"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(location["hours"].replace("|", " "))
            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        yield item
