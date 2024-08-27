from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BricksMinifigsCAUSSpider(WPStoreLocatorSpider):
    name = "bricks_minifigs_ca_us"
    item_attributes = {
        "brand_wikidata": "Q109329121",
        "brand": "Bricks & Minifigs",
        "extras": Categories.SHOP_TOYS.value,
    }
    allowed_domains = [
        "bricksandminifigs.com",
    ]
    days = DAYS_EN
