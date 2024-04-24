from locations.categories import Categories
from locations.storefinders.yext import YextSpider


class PrimantiBrosUSSpider(YextSpider):
    name = "primanti_bros_us"
    item_attributes = {"brand": "Primanti Bros", "brand_wikidata": "Q7243049", "extras": Categories.RESTAURANT.value}
    api_key = "7515c25fc685bbdd7c5975b6573c6912"
    api_version = "20220511"

    def parse_item(self, item, location):
        if "test-location" in item["ref"]:
            return
        item["ref"] = location.get("c_pagesURL")
        item["name"] = location.get("c_searchName")
        item["website"] = location.get("c_pagesURL")
        item.pop("twitter", None)
        yield item
