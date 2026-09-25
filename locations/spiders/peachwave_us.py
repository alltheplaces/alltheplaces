from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PeachwaveUSSpider(WPStoreLocatorSpider):
    name = "peachwave_us"
    item_attributes = {"brand": "Peachwave", "brand_wikidata": "Q109329113"}
    allowed_domains = ["peachwaveyogurt.com"]
    start_urls = [
        "https://peachwaveyogurt.com/wp-admin/admin-ajax.php?action=store_search&autoload=1&lat=39.8283&lng=-98.5795"
    ]
    days = DAYS_EN
    requires_proxy = True

    active_store_ids: set[int] = set()

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://peachwaveyogurt.com/wp-json/wp/v2/wpsl_stores?per_page=100&_fields=id,class_list",
            callback=self.parse_store_index,
        )

    def parse_store_index(self, response: TextResponse) -> Iterable[JsonRequest]:
        self.active_store_ids = {
            store["id"]
            for store in response.json()
            if "wpsl_store_category-coming-soon" not in store.get("class_list", [])
        }
        yield from self.start_requests_all_at_once_method()

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if (
            feature["id"] not in self.active_store_ids
            or feature.get("country") != "United States"
            or not item.get("street_address")
        ):
            return

        item["branch"] = item.pop("name")
        apply_category(Categories.ICE_CREAM, item)
        item["extras"]["cuisine"] = "frozen_yogurt"
        yield item
