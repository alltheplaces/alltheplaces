from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.dict_parser import DictParser
from locations.items import Feature


class GogaStoreLocatorSpider(Spider):
    """
    Goga Store Locator is a software-as-a-service store locator API with an official homepage of https://www.goga.co.jp/products/storelocator/.

    To use this spider, specify a URL in the 'start_urls' list attribute.
    Usually the expected URL is similar to
    "https://map.beisia.co.jp/api/points".

    Optionally, provide a list of geohashes if the base URL does not return all locations.

    Also, you can provide a website formatter, which should be needed for most chains.
    Some of them will provide their own URLs in the JSON response.
    """

    dataset_attributes: dict = {"source": "api"}

    start_urls: list[str] = []
    geohashes: list[str] = []
    website_formatter: str = ""

    async def start(self) -> AsyncIterator[Request]:
        if len(self.start_urls) == 1 and len(self.geohashes) == 0:
            yield Request(url=self.start_urls[0])
        elif len(self.start_urls) == 1 and len(self.geohashes) != 0:
            for geohash in self.geohashes:
                yield Request(
                    url=f"{self.start_urls[0]}/{geohash}"
                )  # make sure to leave out trailing slash on start_urls
        else:
            raise ValueError("Specify one URL in the start_urls list attribute.")
            return

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json()["items"]: # ty: ignore[unresolved-attribute]
            location.update(location.pop("extra_fields"))
            item = DictParser.parse(location)
            if self.website_formatter:
                item["website"] = self.website_formatter.format(location.get("key"))
            item["ref"] = location.get("key")

            yield from self.post_process_feature(item, location)

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        yield item
