from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.items import Feature

# https://location-cloud.navitime.co.jp/


class LocationCloudSpider(Spider):
    dataset_attributes: dict = {"source": "api"}

    api_endpoint: str
    website_formatter: str = ""

    async def start(self) -> AsyncIterator[Request]:
        yield self._get_page(0)

    def _get_page(self, offset: int):
        return Request(
            "{}?datum=wgs84&limit=500&offset={}".format(self.api_endpoint, offset),
            meta={"offset": offset},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()  # ty: ignore[unresolved-attribute]

        for location in data["items"]:
            item = Feature()
            if self.website_formatter:
                item["website"] = self.website_formatter.format(location["code"])
            item["ref"] = location["code"]
            item["lat"] = location["coord"]["lat"]
            item["lon"] = location["coord"]["lon"]
            item["addr_full"] = location.get("address_name")
            item["postcode"] = location.get("postal_code")

            yield from self.post_process_feature(item, location)

        if data["count"]["offset"] + data["count"]["limit"] < data["count"]["total"]:
            yield self._get_page(data["count"]["limit"] + response.meta["offset"])

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        yield item
