from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider
from locations.categories import Categories


class BrowArt23USSpider(AgileStoreLocatorSpider):
    name = "brow_art_23_us"
    item_attributes = {"brand_wikidata": "Q115675881", "brand": "Brow Art 23", "extras": Categories.SHOP_BEAUTY.value}
    allowed_domains = [
        "browart23.com",
    ]
    # We see TCP connection timed out: 110: Connection timed out when fetching robots.txt
    # Attempt to skip fetching it
    custom_settings = {"ROBOTSTXT_OBEY": False}
