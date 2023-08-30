from locations.storefinders.freshop import FreshopSpider


class FoodFairMarketUS(FreshopSpider):
    name = "food_fair_market_us"
    item_attributes = {"brand": "Food Fair Market", "brand_wikidata": "Q122080459"}
    app_key = "foodfair_market"
