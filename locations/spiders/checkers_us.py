from locations.categories import Categories
from locations.storefinders.yext_search import YextSearchSpider


class CheckersUSSpider(YextSearchSpider):
    name = "checkers_us"
    item_attributes = {"brand": "Checkers", "brand_wikidata": "Q63919315", "extras": Categories.FAST_FOOD.value}
    host = "https://locations.checkers.com"

    def parse_item(self, location, item):
        if location["profile"].get("c_alphaNumericStoreID"):
            item["ref"] = location["profile"]["c_alphaNumericStoreID"]
        yield item
