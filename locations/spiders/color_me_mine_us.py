from typing import Iterable

from scrapy.http import Response

from locations.categories import apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider

# Color Me Mine runs the WP Store Locator plugin. The endpoint caps an
# autoload=1 request at 50 locations, so a single wide radius search centred on
# the contiguous US is used instead, which returns every location in one
# request. The response carries a few Canadian and Costa Rican studios, plus
# rows for studios that have not opened yet, all of which are dropped.


class ColorMeMineUSSpider(WPStoreLocatorSpider):
    name = "color_me_mine_us"
    item_attributes = {"brand": "Color Me Mine", "brand_wikidata": "Q121433027"}
    allowed_domains = ["www.colormemine.com"]
    start_urls = [
        "https://www.colormemine.com/wp-admin/admin-ajax.php?action=store_search&lat=39.8283&lng=-98.5795&max_results=500&search_radius=5000"
    ]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if (feature.get("country") or "").strip() not in ["United States", "USA", "US"]:
            return

        # Studios that have not opened yet are listed as "<city>, <state> - Coming Soon!"
        if "coming soon" in (item.get("name") or "").lower():
            return

        item["ref"] = feature["id"]
        item["branch"] = item.pop("name", None)
        item["website"] = feature.get("url")

        apply_category({"amenity": "training", "training": "ceramics_painting"}, item)

        yield item
