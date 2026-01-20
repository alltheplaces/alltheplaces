from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingCOSpider(JSONBlobSpider):
    name = "burger_king_co"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = [
        "https://api-bk-co-a.tillster.com/mobilem8-web-service/rest/storeinfo/distance?latitude=4.0&longitude=-72.0&maxResults=100&radius=1200&radiusUnit=km&statuses=ACTIVE&tenant=bk-co"
    ]
    locations_key = ["getStoresResult", "stores"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = item.pop("name").split("-")[-1]
        item["street_address"] = item.pop("street")
        apply_category(Categories.FAST_FOOD, item)
        yield item
