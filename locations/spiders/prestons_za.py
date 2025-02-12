from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PrestonsZASpider(WPStoreLocatorSpider):
    name = "prestons_za"
    item_attributes = {"brand": "Prestons Liquor Stores", "brand_wikidata": "Q116861728"}
    allowed_domains = ["prestonsliquors.co.za"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["street_address"] = feature.get("address")
        item.pop("addr_full", None)
        item["city"] = feature.get("address2")

        apply_category(Categories.SHOP_ALCOHOL, item)

        yield item
