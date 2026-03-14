from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class LaPorchettaAUNZSpider(WPStoreLocatorSpider):
    name = "la_porchetta_au_nz"
    item_attributes = {"brand": "La Porchetta", "brand_wikidata": "Q6464528"}
    allowed_domains = ["laporchetta.com.au"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        if feature["country"] == "New Zealand":
            item.pop("state", None)
        apply_category(Categories.RESTAURANT, item)
        yield item
