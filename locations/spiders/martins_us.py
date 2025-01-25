from locations.categories import Categories, apply_category
from locations.storefinders.freshop import FreshopSpider


class MartinsUSSpider(FreshopSpider):
    name = "martins_us"
    item_attributes = {"brand": "Martin's Super Markets", "brand_wikidata": "Q6774803"}
    app_key = "martins"

    def parse_item(self, item, location):
        item["branch"] = item.pop("name")

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
