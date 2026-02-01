from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EasyLocatorSpider(JSONBlobSpider):
    """
    EasyLocator is a cloud-hosted store locator service with an official
    website of https://easylocator.net/

    To use this spider, specify api_brand_name as the brand name key existing
    in calls to the Easy Locator API at https://easylocator.net/ajax/...

    Example source URL: https://easylocator.net/ajax/search_by_lat_lon_geojson/gigiscupcakesusa/-37.86/144.9717/0/10/null/null
    Example api_brand_name from source URL: gigiscupcakesusa
    """

    dataset_attributes: dict = {"source": "api", "api": "easylocator.net"}
    api_brand_name: str
    loations_key: str | list[str] = "physical"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=f"https://easylocator.net/ajax/search_by_lat_lon_geojson/{self.api_brand_name}/0/0/0/null/null/null"
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["postcode"] = feature["properties"]["zip_postal_code"]
        yield from self.parse_item(item, feature) or []

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        yield item
