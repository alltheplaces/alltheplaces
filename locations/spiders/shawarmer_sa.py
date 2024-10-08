from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ShawarmerSASpider(WPStoreLocatorSpider):
    name = "shawarmer_sa"
    item_attributes = {"brand_wikidata": "Q29509653", "brand": "شاورمر", "extras": Categories.FAST_FOOD.value}
    allowed_domains = [
        "www.shawarmer.com",
    ]
    days = DAYS_EN
