from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class FazolisUSSpider(WPStoreLocatorSpider):
    name = "fazolis_us"
    item_attributes = {"brand": "Fazoli's", "brand_wikidata": "Q1399195", "extras": Categories.FAST_FOOD.value}
    allowed_domains = [
        "fazolis.com",
    ]
    iseadgg_countries_list = ["US"]
    search_radius = 100
    max_results = 50
    days = DAYS_EN
