import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider

# Brake Masters runs the WP Store Locator plugin, but from a renamed admin
# directory (/brakemasters-admin/ rather than /wp-admin/), so start_urls is set
# explicitly. The endpoint returns every location in one autoload request.


class BrakeMastersUSSpider(WPStoreLocatorSpider):
    name = "brake_masters_us"
    item_attributes = {"brand": "Brake Masters", "brand_wikidata": "Q4956024"}
    allowed_domains = ["www.brakemasters.com"]
    start_urls = ["https://www.brakemasters.com/brakemasters-admin/admin-ajax.php?action=store_search&autoload=1"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        # "Brake Masters Store #254" / "Brake Masters #125"
        if not (store_number := re.search(r"#\s*(\d+)", item.get("name") or "")):
            return
        item["ref"] = store_number.group(1)
        item["branch"] = None
        item["name"] = None

        item["website"] = feature.get("store_page_url")

        apply_category(Categories.SHOP_CAR_REPAIR, item)
        apply_yes_no(Extras.VEHICLE_BRAKE_SERVICES, item, True)

        yield item
