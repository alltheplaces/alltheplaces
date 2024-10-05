from locations.categories import Categories
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class FazolisUSSpider(WPStoreLocatorSpider):
    name = "fazolis_us"
    item_attributes = {"brand": "Fazoli's", "brand_wikidata": "Q1399195", "extras": Categories.FAST_FOOD.value}
    allowed_domains = [
        "fazolis.com",
    ]
