from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class FoodlandGroceryUSSpider(AgileStoreLocatorSpider):
    name = "foodland_grocery_us"
    item_attributes = {
        "brand_wikidata": "Q5465271",
        "brand": "FoodLand",
    }
    allowed_domains = [
        "www.foodlandgrocery.com",
    ]
