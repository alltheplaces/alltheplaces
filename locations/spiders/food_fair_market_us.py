from locations.categories import Categories
from locations.storefinders.freshop import FreshopSpider


class FoodFairMarketUSSpider(FreshopSpider):
    name = "food_fair_market_us"
    item_attributes = {
        "brand": "Food Fair Market",
        "brand_wikidata": "Q122080459",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    app_key = "foodfair_market"
