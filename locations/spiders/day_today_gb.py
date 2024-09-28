from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DayTodayGBSpider(WPStoreLocatorSpider):
    name = "day_today_gb"
    item_attributes = {
        "brand": "Day-Today",
        "brand_wikidata": "Q121435331",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }
    allowed_domains = ["www.day-today.co.uk"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = item["name"].title()
        yield item
