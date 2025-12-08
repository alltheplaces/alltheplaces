from locations.categories import Categories
from locations.hours import DAYS_DE
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CaderaDESpider(WPStoreLocatorSpider):
    name = "cadera_de"
    item_attributes = {"brand_wikidata": "Q62086410", "brand": "Cadera", "extras": Categories.SHOP_BAKERY.value}
    allowed_domains = [
        "cadera.de",
    ]
    days = DAYS_DE
