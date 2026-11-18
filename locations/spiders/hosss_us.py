from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class HosssUSSpider(WPStoreLocatorSpider):
    name = "hosss_us"
    item_attributes = {"brand": "Hoss's Steak & Sea House", "brand_wikidata": "Q5908897"}
    allowed_domains = ["hosss.com"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        yield item
