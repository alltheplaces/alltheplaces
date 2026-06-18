from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class RidleysFamilyMarketsSpider(JSONBlobSpider):
    name = "ridleys_family_markets"
    item_attributes = {"brand": "Ridley's Family Markets", "brand_wikidata": "Q7332999"}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://shopridleys.com/wp-admin/admin-ajax.php",
            body="action=imm_sections_get_stores_ajax&nonce=43299e3cf7&lat=41.3080357&lng=-105.5557724&city=&count=100&all_store=yes",
            method="POST",
        )

    def extract_json(self, response: Response) -> list[dict]:
        return response.json().get("data", {}).get("data", {}).get("message", [])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["country"] = "US"
        item["street_address"] = item.pop("addr_full")
        item["branch"] = feature.get("DisplayName")
        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
