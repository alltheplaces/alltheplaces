import re
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse
from scrapy_playwright.page import PageMethod

from locations.categories import apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PkEquipmentUSSpider(WPStoreLocatorSpider, PlaywrightSpider):
    name = "pk_equipment_us"
    item_attributes = {"brand": "P&K Equipment"}
    start_urls = [
        "https://www.pkequipment.com/wp-admin/admin-ajax.php?action=store_search&lat=35.5&lng=-96.5&max_results=100&search_radius=500"
    ]
    days = DAYS_EN
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=self.start_urls[0],
            meta={
                "playwright_page_methods": [
                    PageMethod("wait_for_url", lambda url: "sgcaptcha" not in url),
                ]
            },
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        slug = re.sub(r"[^a-z0-9]+", "-", feature["store"].lower()).strip("-")
        item["website"] = f"https://www.pkequipment.com/{slug}/"
        apply_category({"shop": "tractor"}, item)
        yield item
