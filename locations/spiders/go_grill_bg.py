from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class GoGrillBGSpider(WPStoreLocatorSpider):
    name = "go_grill_bg"
    item_attributes = {"brand": "Go Grill", "brand_wikidata": "Q122839782"}
    allowed_domains = ["gogrill.bg"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("GO GRILL • ")
        item["website"] = None

        apply_category(Categories.RESTAURANT, item)

        yield item
