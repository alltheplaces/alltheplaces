from locations.categories import Categories
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class BlueBottleLiquorsZASpider(AgileStoreLocatorSpider):
    name = "blue_bottle_liquors_za"
    item_attributes = {
        "brand": "Blue Bottle Liquors",
        "brand_wikidata": "Q116861688",
        "extras": Categories.SHOP_ALCOHOL.value,
    }

    allowed_domains = [
        "bluebottleliquors.co.za",
    ]

    def parse_item(self, item, location):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        item["name"] = self.item_attributes["brand"]
        yield item
