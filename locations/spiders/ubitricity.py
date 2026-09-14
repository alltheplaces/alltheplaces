from typing import Any, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class UbitricitySpider(JSONBlobSpider):
    name = "ubitricity"
    item_attributes = {"brand": "ubitricity", "brand_wikidata": "Q113699692"}
    api_url = "https://api.shell.com/ubitricity/direct-access/api/direct-access/locations"
    start_urls = [f"{api_url}?pageNumber=1&pageSize=200"]
    locations_key = "data"

    def parse(self, response: Response, **kwargs: Any) -> Iterable[JsonRequest | Feature]:
        yield from super().parse(response)
        data = response.json()
        if data["currentPage"] < data["totalPages"]:
            yield JsonRequest(url=f"{self.api_url}?pageNumber={data['currentPage'] + 1}&pageSize=200")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature.get("coordinates"):
            return
        item["ref"] = feature["cpoLocationId"]
        apply_category(Categories.CHARGING_STATION, item)
        yield item
