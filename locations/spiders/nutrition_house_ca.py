from locations.categories import Categories
from locations.storefinders.storeify import StoreifySpider


class NutritionHouseCASpider(StoreifySpider):
    name = "nutrition_house_ca"
    item_attributes = {
        "brand": "Nutrition House",
        "brand_wikidata": "Q112966431",
        "extras": Categories.SHOP_NUTRITION_SUPPLEMENTS.value,
    }
    api_key = "nutrition-house-canada.myshopify.com"
