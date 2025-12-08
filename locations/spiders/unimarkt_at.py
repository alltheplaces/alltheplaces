from locations.categories import Categories
from locations.hours import DAYS_DE
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class UnimarktATSpider(WPStoreLocatorSpider):
    name = "unimarkt_at"
    item_attributes = {"brand_wikidata": "Q1169599", "brand": "Unimarkt", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = [
        "unimarkt.at",
    ]
    days = DAYS_DE
