from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class KingTacoUSSpider(WPStoreLocatorSpider):
    name = "king_taco_us"
    item_attributes = {"brand_wikidata": "Q6412104", "brand": "King Taco", "extras": Categories.FAST_FOOD.value}
    allowed_domains = [
        "kingtaco.com",
    ]
    days = DAYS_EN
