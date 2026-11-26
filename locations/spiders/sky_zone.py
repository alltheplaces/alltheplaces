from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SkyZoneSpider(WPStoreLocatorSpider):
    name = "sky_zone"
    item_attributes = {"brand": "Sky Zone", "brand_wikidata": "Q7537557"}
    start_urls = [
        "https://skyzone.com/wp-admin/admin-ajax.php?action=store_search&autoload=1&lat=43.6541625&lng=-70.2802368"
    ]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = feature["park_url"]
        apply_category(Categories.LEISURE_TRAMPOLINE_PARK, item)
        yield item
