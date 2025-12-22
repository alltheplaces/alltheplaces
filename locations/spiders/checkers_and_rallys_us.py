from locations.categories import Categories, apply_category
from locations.storefinders.yext_search import YextSearchSpider


class CheckersAndRallysUSSpider(YextSearchSpider):
    name = "checkers_and_rallys_us"
    host = "https://locations.checkersandrallys.com"
    brands = {
        "Checkers": {"brand": "Checkers", "brand_wikidata": "Q63919315"},
        "Rally's": {"brand": "Rally's", "brand_wikidata": "Q63919323"},
    }

    def parse_item(self, location, item):
        if "CLOSED" in item.get("name", "").upper():
            return

        if location["profile"].get("c_alphaNumericStoreID"):
            item["ref"] = location["profile"]["c_alphaNumericStoreID"]

        if "Checkers" in location["profile"].get("brands", []):
            item["brand"] = self.brands["Checkers"]["brand"]
            item["brand_wikidata"] = self.brands["Checkers"]["brand_wikidata"]
        elif "Rally's" in location["profile"].get("brands", []):
            item["brand"] = self.brands["Rally's"]["brand"]
            item["brand_wikidata"] = self.brands["Rally's"]["brand_wikidata"]
        elif len(location["profile"].get("brands", [])) >= 1:
            raise ValueError("Unknown brand detected: {}".format(", ".join(location["profile"]["brands"])))

        apply_category(Categories.FAST_FOOD, item)
        yield item
