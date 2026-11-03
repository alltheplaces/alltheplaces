from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SuzukiFRSpider(JSONBlobSpider):
    name = "suzuki_fr"
    item_attributes = {"brand": "Suzuki", "brand_wikidata": "Q181642"}
    locations_key = "stores"

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in country_iseadgg_centroids("FR", 48):
            yield self.make_request(lat, lon)

    def make_request(self, lat: float, lon: float) -> JsonRequest:
        return JsonRequest(f"https://www.suzuki.fr/ajax-store-result?c={lat};{lon}")

    def parse(self, response: TextResponse) -> Iterable[Feature | JsonRequest]:
        yield from super().parse(response)
        # Results are truncated, so search again around each dealer found
        for store in self.extract_json(response):
            yield self.make_request(store["lat"], store["lng"])

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["code"]
        item["street_address"] = item.pop("addr_full")
        item["website"] = feature["url"] or f"https://www.suzuki.fr/store/show/{feature['slug']}"
        apply_category(Categories.SHOP_CAR, item)
        yield item
