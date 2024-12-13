from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class VanWallUSSpider(WPStoreLocatorSpider):
    name = "van_wall_us"
    item_attributes = {"name": "Van Wall", "brand": "Van Wall"}
    allowed_domains = ["vanwall.com"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Van Wall Equipment – ")

        apply_category(Categories.SHOP_TOOL_HIRE, item)

        yield item
