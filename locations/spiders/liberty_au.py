from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class LibertyAUSpider(WPStoreLocatorSpider):
    name = "liberty_au"
    item_attributes = {"brand": "Liberty", "brand_wikidata": "Q106687078"}
    allowed_domains = ["www.libertyconvenience.com.au"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        apply_category(Categories.FUEL_STATION, item)
        yield item
