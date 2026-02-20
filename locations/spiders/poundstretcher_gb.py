from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.shopapps import ShopAppsSpider

BARGAIN_BUYS = {"brand": "Bargain Buys", "brand_wikidata": "Q19870995"}
POUNDSTRETCHER = {"brand": "Poundstretcher", "brand_wikidata": "Q7235675"}


class PoundstretcherGBSpider(ShopAppsSpider):
    name = "poundstretcher_gb"
    item_attributes = POUNDSTRETCHER
    key = "pound-stretcher-store.myshopify.com"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item.pop("email")  # Emails always the same
        item["branch"] = item.pop("name")
        item["website"] = location["website"].replace("pound-stretcher-store.myshopify.com", "poundstretcher.co.uk")

        if item["branch"].endswith(" Bargain Buys"):
            item["branch"] = item["branch"].removesuffix(" Bargain Buys")
            item.update(BARGAIN_BUYS)

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(location.get("hours", ""))

        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item
