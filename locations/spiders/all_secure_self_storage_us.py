from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class AllSecureSelfStorageUSSpider(StoreLocatorWidgetsSpider):
    name = "all_secure_self_storage_us"
    item_attributes = {"brand": "All Secure Self Storage", "brand_wikidata": "Q119141885"}
    key = "27e9068ee54b279b61f3d6dbf0fbdb74"

    def parse_item(self, item, location):
        if "COMING SOON" in item["name"].upper():
            return
        item.pop("website")
        hours_string = ""
        for day_name in DAYS_FULL:
            if location["data"].get(f"hours_{day_name}"):
                time_range = location["data"].get(f"hours_{day_name}")
                hours_string = f"{hours_string} {day_name}: {time_range}"
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
