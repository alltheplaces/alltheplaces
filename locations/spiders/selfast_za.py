from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SelfastZASpider(WPStoreLocatorSpider):
    name = "selfast_za"
    item_attributes = {"brand_wikidata": "Q116861449", "brand": "Selfast", "extras": Categories.SHOP_CLOTHES.value}
    allowed_domains = ["shop.selfast.co.za"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("street_address", None)
        item["branch"] = item.pop("name")
        yield item
