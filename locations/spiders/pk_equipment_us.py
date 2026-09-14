import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PkEquipmentUSSpider(WPStoreLocatorSpider):
    name = "pk_equipment_us"
    item_attributes = {"brand": "P&K Equipment"}
    allowed_domains = ["www.pkequipment.com"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        slug = re.sub(r"[^a-z0-9]+", "-", feature["store"].lower()).strip("-")
        item["website"] = f"https://www.pkequipment.com/{slug}/"
        apply_category({"shop": "tractor"}, item)
        yield item
