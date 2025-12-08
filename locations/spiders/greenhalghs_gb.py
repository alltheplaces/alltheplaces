from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class GreenhalghsGBSpider(WPStoreLocatorSpider):
    name = "greenhalghs_gb"
    item_attributes = {"brand": "Greenhalgh's", "brand_wikidata": "Q99939079", "extras": Categories.SHOP_BAKERY.value}
    allowed_domains = ["www.greenhalghs.com"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("addr_full", None)
        item["street_address"] = feature.get("address2")
        if item["website"] and item["website"].startswith("/"):
            item["website"] = "https://www.greenhalghs.com" + item["website"]
        yield item
