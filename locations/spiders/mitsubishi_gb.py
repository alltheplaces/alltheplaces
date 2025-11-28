from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.mitsubishi import MitsubishiSpider
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MitsubishiGBSpider(WPStoreLocatorSpider):
    name = "mitsubishi_gb"
    item_attributes = MitsubishiSpider.item_attributes
    allowed_domains = ["mitsubishi-motors.co.uk"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
