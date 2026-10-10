from locations.categories import Categories, apply_category
from locations.storefinders.storepoint import StorepointSpider


class QqNailSpaUSSpider(StorepointSpider):
    name = "qq_nail_spa_us"
    item_attributes = {"brand": "QQ Nails & Spa", "name": "QQ Nails & Spa"}
    key = "16543d6401ccff"

    def parse_item(self, item, location):
        if "Coming Soon" in location["name"]:
            return

        item["ref"] = location["public_id"]
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_BEAUTY, item)
        yield item
