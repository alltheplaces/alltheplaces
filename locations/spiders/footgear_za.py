from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class FootgearZASpider(WPStoreLocatorSpider):
    name = "footgear_za"
    item_attributes = {"brand": "Footgear", "brand_wikidata": "Q116290280", "extras": Categories.SHOP_SHOES.value}
    allowed_domains = ["www.footgear.co.za"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        yield item
