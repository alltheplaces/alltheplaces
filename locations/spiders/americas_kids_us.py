from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class AmericasKidsUSSpider(StoreLocatorWidgetsSpider):
    name = "americas_kids_us"
    brands = {
        "Americas Kids": {"brand": "America's Kids", "brand_wikidata": "Q119141496"},
        "Kids World": {"brand": "Kids World", "brand_wikidata": "Q119141647"},
        "Lazarus": {"brand": "Lazarus", "brand_wikidata": "Q119141646"},
        "Young Land": {"brand": "Young Land", "brand_wikidata": "Q119141643"},
        "Young World": {"brand": "Young World", "brand_wikidata": "Q119141641"},
    }
    key = "8b5da83104f650ef1c1194d92228c489"

    def parse_item(self, item, location):
        for brand_key, brand_details in self.brands.items():
            if brand_key in location["name"]:
                item.update(brand_details)
                break
        item.pop("image")
        hours_string = ""
        for day_name in DAYS_FULL:
            if location["data"].get(f"hours_{day_name}"):
                time_range = location["data"].get(f"hours_{day_name}")
                hours_string = f"{hours_string} {day_name}: {time_range}"
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
