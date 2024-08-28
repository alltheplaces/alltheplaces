from locations.categories import Categories
from locations.hours import DAYS_FR
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MonsieurStoreFRSpider(WPStoreLocatorSpider):
    name = "monsieur_store_fr"
    item_attributes = {
        "brand_wikidata": "Q113686692",
        "brand": "Monsieur Store",
        "extras": Categories.SHOP_WINDOW_BLIND.value,
    }
    allowed_domains = [
        "monsieurstore.com",
    ]
    days = DAYS_FR
