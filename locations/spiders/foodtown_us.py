from locations.hours import OpeningHours
from locations.storefinders.freshop import FreshopSpider


class FoodtownUSSpider(FreshopSpider):
    name = "foodtown_us"
    item_attributes = {"brand": "Foodtown", "brand_wikidata": "Q5465575"}
    app_key = "foodtown"

    def parse_item(self, item, location):
        if "Store:" in item["phone"]:
            item["phone"] = item["phone"].replace("Store: ", "").split("\n")[0]
        if "7 DAYS" in location.get("hours_md", "").upper():
            hours_string = location["hours_md"].upper().replace("7 DAYS A WEEK", "Mon-Sun")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
