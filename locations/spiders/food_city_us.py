from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class FoodCityUSSpider(WPStoreLocatorSpider):
    name = "food_city_us"
    item_attributes = {"brand": "Food City", "brand_wikidata": "Q16981107"}
    allowed_domains = ["myfoodcity.com"]
    requires_proxy = True
    time_format = "%I:%M %p"
