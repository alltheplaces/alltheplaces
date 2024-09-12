from locations.categories import Categories
from locations.hours import DAYS_NL
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class Optie1NLSpider(WPStoreLocatorSpider):
    name = "optie1_nl"
    item_attributes = {"brand_wikidata": "Q62393564", "brand": "Optie1", "extras": Categories.SHOP_MOBILE_PHONE.value}
    allowed_domains = [
        "www.optie1.nl",
    ]
    days = DAYS_NL
