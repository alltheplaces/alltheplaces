from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AugustusGelateryAUSpider(WPStoreLocatorSpider):
    name = "augustus_gelatery_au"
    item_attributes = {"brand": "Augustus Gelatery", "brand_wikidata": "Q141237454"}
    allowed_domains = ["augustusgelatery.com.au"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")

        apply_category(Categories.ICE_CREAM, item)

        yield item
