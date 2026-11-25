from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SanelNapaUSSpider(WPStoreLocatorSpider):
    name = "sanel_napa_us"
    item_attributes = {"brand": "Sanel NAPA", "brand_wikidata": "Q122564780"}
    start_urls = [
        "https://sanelnapa.com/wp-admin/admin-ajax.php?action=store_search&lat=29.7604267&lng=-95.3698028&autoload=1"
    ]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("NAPA ")
        apply_category(Categories.SHOP_CAR_PARTS, item)
        yield item
