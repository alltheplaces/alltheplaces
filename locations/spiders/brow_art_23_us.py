from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class BrowArt23USSpider(AgileStoreLocatorSpider):
    name = "brow_art_23_us"
    item_attributes = {"brand": "Brow Art 23", "brand_wikidata": "Q115675881"}
    allowed_domains = ["www.browart23.com"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removesuffix(" (Franchise)")
        item["addr_full"] = item.pop("street_address")
        # Every store has placeholder "0" hours for all days, not real closures
        item.pop("opening_hours")
        item.pop("website")
        apply_category(Categories.SHOP_BEAUTY, item)
        yield item
