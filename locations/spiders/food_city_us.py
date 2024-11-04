from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class FoodCityUSSpider(WPStoreLocatorSpider):
    name = "food_city_us"
    item_attributes = {
        "brand": "Food City",
        "brand_wikidata": "Q130253202",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["mifoodcity.com"]
    days = DAYS_EN
