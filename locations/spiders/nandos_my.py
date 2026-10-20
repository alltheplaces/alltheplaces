from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES


class NandosMYSpider(JSONBlobSpider):
    name = "nandos_my"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    start_urls = ["https://nandos.com.my/restaurants/__data.json"]

    def extract_json(self, response: Response) -> list[dict]:
        features = []
        for node in response.json()["nodes"]:
            if not node or "data" not in node:
                continue
            root = self.resolve(node["data"], 0)
            for group in (root or {}).get("restaurantsByState") or []:
                features.extend(group["restaurants"])
        return features

    def resolve(self, data: list, index: Any) -> Any:
        """Resolve a value from a SvelteKit "devalue" indexed payload."""
        if not isinstance(index, int) or not 0 <= index < len(data):
            return None
        value = data[index]
        if isinstance(value, dict):
            return {key: self.resolve(data, i) for key, i in value.items()}
        if isinstance(value, list):
            return [self.resolve(data, i) for i in value]
        return value

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request | Feature]:
        item["branch"] = item.pop("name")
        item["phone"] = feature.get("storeContactNumber")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            (feature.get("storeOpeningHours") or "").replace("Everyday", "Mo-Su")
        )
        apply_category(Categories.RESTAURANT, item)
        if maps_url := feature.get("googleMapsUrl"):
            yield Request(
                url=maps_url,
                meta={"item": item, "dont_redirect": True, "handle_httpstatus_list": [301, 302]},
                callback=self.parse_coordinates,
                dont_filter=True,
            )
        else:
            yield item

    def parse_coordinates(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        if location := response.headers.get("Location"):
            coordinates = url_to_coords(location.decode())
            if coordinates != (None, None):
                item["lat"], item["lon"] = coordinates
        yield item
