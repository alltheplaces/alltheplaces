from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DoorsPlusAUSpider(WPStoreLocatorSpider):
    name = "doors_plus_au"
    item_attributes = {"brand": "Doors Plus", "brand_wikidata": "Q78945358"}
    allowed_domains = ["www.doorsplus.com.au"]
    time_format = "%I:%M %p"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_DOORS, item)
        yield item
