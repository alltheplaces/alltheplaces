from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class DirtCheapUSSpider(AgileStoreLocatorSpider):
    name = "dirt_cheap_us"
    item_attributes = {
        "brand": "Dirt Cheap",
        "brand_wikidata": "Q123013019",
        "extras": Categories.SHOP_VARIETY_STORE.value,
    }
    allowed_domains = ["ilovedirtcheap.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["website"] = "https://ilovedirtcheap.com/locations/store-details/" + feature["slug"]
        item["image"] = feature.get("storephoto")
        yield item
