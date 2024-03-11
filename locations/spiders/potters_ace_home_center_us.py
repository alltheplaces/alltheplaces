from locations.categories import Categories
from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class PottersAceHomeCenterUSSpider(StoreLocatorWidgetsSpider):
    name = "potters_ace_home_center_us"
    item_attributes = {
        "brand": "Potter's Ace Home Center",
        "brand_wikidata": "Q119141289",
        "extras": Categories.SHOP_DOITYOURSELF.value,
    }
    key = "5b64c14c90736e1bdbdc612010148f0d"

    def parse_item(self, item, location):
        item.pop("email")
        item.pop("website")
        item.pop("image")
        hours_string = ""
        for day_name in DAYS_FULL:
            if location["data"].get(f"hours_{day_name}"):
                time_range = location["data"].get(f"hours_{day_name}")
                hours_string = f"{hours_string} {day_name}: {time_range}"
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
