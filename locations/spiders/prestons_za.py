from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PrestonsZASpider(WPStoreLocatorSpider):
    name = "prestons_za"
    item_attributes = {
        "brand": "Prestons",
        "brand_wikidata": "Q116861728",
        "extras": Categories.SHOP_ALCOHOL.value,
    }
    allowed_domains = ["prestonsliquors.co.za"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["street_address"] = feature.get("address")
        item.pop("addr_full", None)
        item["city"] = feature.get("address2")
        yield item
