from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.spiders.mitsubishi import MitsubishiSpider
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MitsubishiZASpider(WPStoreLocatorSpider):
    name = "mitsubishi_za"
    allowed_domains = ["mitsubishi-motors.co.za"]
    item_attributes = MitsubishiSpider.item_attributes
    start_urls = [
        # autoload=1 still loads all stores but requires coordinates
        "https://mitsubishi-motors.co.za/wp-admin/admin-ajax.php?action=store_search&lat=-25.7478676&lng=28.2292712&autoload=1"
    ]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CAR, item)
        yield item
