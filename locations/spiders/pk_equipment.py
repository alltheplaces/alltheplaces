import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PkEquipmentSpider(WPStoreLocatorSpider):
    name = "pk_equipment"
    item_attributes = {"brand": "P&K Equipment", "extras": {"shop": "tractor"}}
    allowed_domains = ["www.pkequipment.com"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        slug = re.sub(r"[^a-z0-9]+", "-", feature["store"].lower()).strip("-")
        item["website"] = f"https://www.pkequipment.com/{slug}/"
        yield item
