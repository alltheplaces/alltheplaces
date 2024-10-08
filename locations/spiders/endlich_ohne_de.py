from locations.categories import Categories
from locations.hours import DAYS_DE
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class EndlichOhneDESpider(WPStoreLocatorSpider):
    name = "endlich_ohne_de"
    item_attributes = {"brand_wikidata": "Q119982663", "brand": "Endlich Ohne", "extras": Categories.SHOP_BEAUTY.value}
    allowed_domains = [
        "www.endlich-ohne.de",
    ]
    days = DAYS_DE
