from typing import Any, AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class UrbanAirSpider(JSONBlobSpider):
    name = "urban_air"
    item_attributes = {"brand": "Urban Air", "brand_wikidata": "Q110172893"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://www.urbanair.com/wp-json/urbanair-api/locations",
            data={"page": page},
            meta={"page": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(1)

    def extract_json(self, response: TextResponse) -> list[dict]:
        return response.json().get("data") or []

    def parse(self, response: TextResponse, **kwargs: Any) -> Any:
        features = self.extract_json(response)
        yield from self.parse_feature_array(response, features) or []
        if features:
            yield self.make_request(response.meta["page"] + 1)

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = (item.pop("name", None) or "").split(",", 1)[0].strip() or None
        apply_category(Categories.LEISURE_TRAMPOLINE_PARK, item)
        yield item
