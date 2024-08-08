from locations.categories import Categories
from locations.storefinders.yext_search import YextSearchSpider


class RallysUSSpider(YextSearchSpider):
    name = "rallys_us"
    item_attributes = {"brand": "Rally's", "brand_wikidata": "Q63919323", "extras": Categories.FAST_FOOD.value}
    host = "https://locations.rallys.com"

    def parse_item(self, location, item):
        if location["profile"].get("c_alphaNumericStoreID"):
            item["ref"] = location["profile"]["c_alphaNumericStoreID"]
        yield item
