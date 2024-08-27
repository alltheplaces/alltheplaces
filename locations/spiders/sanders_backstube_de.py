from locations.categories import Categories
from locations.hours import DAYS_DE
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SandersBackstubeDESpider(WPStoreLocatorSpider):
    name = "sanders_backstube_de"
    item_attributes = {
        "brand_wikidata": "Q66207337",
        "brand": "sander's backstube",
        "extras": Categories.SHOP_BAKERY.value,
    }
    allowed_domains = [
        "sanders-backstube.de",
    ]
    days = DAYS_DE
