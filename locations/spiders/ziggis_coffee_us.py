from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class ZiggisCoffeeUSSpider(AgileStoreLocatorSpider):
    name = "ziggis_coffee_us"
    item_attributes = {"brand": "Ziggi's Coffee", "brand_wikidata": "Q141067779"}
    allowed_domains = ["ziggiscoffee.com"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        # Closed and "Coming Soon" stores are listed with the open ones.
        if feature.get("store_status") != "Open":
            return
        # The "title" is the street address, not a store name.
        item.pop("name", None)
        if store_number := feature.get("ziggis_store_number"):
            item["ref"] = store_number
        # The plugin's own hours field is empty for nearly every store; the hours are
        # written out in up to three lines such as "Monday - Thursday: 5:00AM - 9:00PM".
        item["opening_hours"] = OpeningHours()
        for key in ("hours_1", "hours_2", "hours_3"):
            if hours := feature.get(key):
                item["opening_hours"].add_ranges_from_string(hours)
        apply_category(Categories.COFFEE_SHOP, item)
        yield item
