from locations.categories import Categories
from locations.hours import DAYS_DE
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BilgroDESpider(WPStoreLocatorSpider):
    name = "bilgro_de"
    item_attributes = {"brand_wikidata": "Q108029888", "brand": "bilgro", "extras": Categories.SHOP_BEVERAGES.value}
    allowed_domains = [
        "www.bilgro.de",
    ]
    days = DAYS_DE
