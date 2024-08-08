import html
import re

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class ThePlantbaseStoreGBSpider(StoreLocatorWidgetsSpider):
    name = "the_plantbase_store_gb"
    item_attributes = {"brand": "The Plantbase Store", "brand_wikidata": "Q119157083"}
    key = "a1516366f107908d0d6c67a258b2bae8"

    def parse_item(self, item, location):
        item["name"] = re.sub(r"\s+", " ", html.unescape(item["name"]))
        if "Plantbase" not in location["filters"]:
            return
        hours_raw = re.sub(r"\s+", " ", location["data"]["description"]).replace("Daily", "Mon - Sun")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_raw)
        item.pop("website")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
