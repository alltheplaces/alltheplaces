from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.items import Feature


class LimesharpStoreLocatorSpider(Spider):
    """
    Source code and some limited documentation for the Limesharp Store Locator
    (also known as "Stockists") is available from:
    https://github.com/motou/magento2-store-locator-stockists-extension

    To use this store finder, specify allowed_domains = ["example.net"] and
    the default path for the Limesharp Store Locator API endpoint will be
    used. In the event the default path is different, you can alternatively
    specify start_urls =
    ["https://example.net/custom-path/stockists/ajax/stores/"].

    If clean ups or additional field extraction is required from the source
    data, override the parse_item function. Two parameters are passed:
        item: an ATP "Feature" class.
        location: a dictionary which is returned from the store locator JSON
                  response for a particular location.
    """

    allowed_domains: list[str] = []
    start_urls: list[str] = []

    async def start(self) -> AsyncIterator[JsonRequest]:
        if len(self.start_urls) == 0 and len(self.allowed_domains) == 1:
            yield JsonRequest(url=f"https://{self.allowed_domains[0]}/stockists/ajax/stores/")
        elif len(self.start_urls) == 1:
            yield JsonRequest(url=self.start_urls[0])
        else:
            raise ValueError(
                "Specify one domain name in the allowed_domains list attribute or one URL in the start_urls list attribute."
            )

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json():
            if (
                not location["name"]
                and not location["latitude"]
                and not location["longitude"]
                and not location["address"]
            ):
                continue
            item = DictParser.parse(location)
            item["ref"] = location["stockist_id"]
            item["street_address"] = location["address"]
            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        yield item
