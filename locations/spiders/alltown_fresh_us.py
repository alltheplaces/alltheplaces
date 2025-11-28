from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AlltownFreshUSSpider(WPStoreLocatorSpider):
    name = "alltown_fresh_us"
    item_attributes = {"brand": "Alltown Fresh", "brand_wikidata": "Q119591365"}
    allowed_domains = ["alltownfresh.com"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
