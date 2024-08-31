from locations.categories import Categories
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class ClothingJunctionZASpider(StoreLocatorWidgetsSpider):
    name = "clothing_junction_za"
    item_attributes = {
        "brand": "Clothing Junction",
        "brand_wikidata": "Q116474981",
        "extras": Categories.SHOP_CLOTHES.value,
    }
    key = "N9yE0tiPbX9Z6diGz7MwPNqBWhMWA2uV"

    def parse_item(self, item, location):
        item["branch"] = item.pop("name")
        item["name"] = self.item_attributes["brand"]
        yield item
