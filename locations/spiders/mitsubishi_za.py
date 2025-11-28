from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.mitsubishi import MitsubishiSpider
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MitsubishiZASpider(WPStoreLocatorSpider):
    name = "mitsubishi_za"
    allowed_domains = ["www.mitsubishi-motors.co.za"]
    item_attributes = MitsubishiSpider.item_attributes

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CAR, item)
        yield item
