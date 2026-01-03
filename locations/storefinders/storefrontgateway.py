from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class StorefrontgatewaySpider(Spider):
    """
    A relatively unknown storefinder, associated with https://mi9retail.com/

    To use, specify a single URL in the `start_urls` list attribute.
    """

    start_urls: list[str] = []

    async def start(self) -> AsyncIterator[JsonRequest]:
        if len(self.start_urls) != 1:
            raise ValueError("Specify one URL in the start_urls list attribute.")
            return
        yield JsonRequest(url=self.start_urls[0])

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json()["items"]:
            self.pre_process_data(location)

            if location.get("status") != "Active":
                continue
            item = DictParser.parse(location)
            item["ref"] = location["retailerStoreId"]
            item["name"] = item["name"].strip()
            item["city"] = item["city"].strip()
            item["street_address"] = clean_address(
                [location.get("addressLine1"), location.get("addressLine2"), location.get("addressLine3")]
            )
            item["state"] = location.get("countyProvinceState")
            if location.get("openingHours"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(location["openingHours"])
            yield from self.post_process_item(item, response, location) or []

    def pre_process_data(self, location: dict, **kwargs) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
