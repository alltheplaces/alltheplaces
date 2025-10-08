import html
import re

from locations.hours import OpeningHours
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class LongdanGBSpider(StoreLocatorWidgetsSpider):
    name = "longdan_gb"
    item_attributes = {"brand": "Longdan", "brand_wikidata": "Q111462402"}
    key = "a1516366f107908d0d6c67a258b2bae8"

    def parse_item(self, item, location):
        item["name"] = re.sub(r"\s+", " ", html.unescape(item["name"]))
        if "Longdan" not in location["filters"]:
            return

        if opening_times := location["data"].get("description"):
            hours_raw = re.sub(r"\s+", " ", opening_times).replace("Daily", "Mon - Sun")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_raw)
        item.pop("website")
        yield item
