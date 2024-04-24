from locations.categories import Categories
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class BrowArt23USSpider(AgileStoreLocatorSpider):
    name = "brow_art_23_us"
    item_attributes = {"brand_wikidata": "Q115675881", "brand": "Brow Art 23", "extras": Categories.SHOP_BEAUTY.value}
    allowed_domains = [
        "browart23.com",
    ]
    requires_proxy = True
