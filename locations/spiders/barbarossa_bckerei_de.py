from locations.hours import DAYS_DE
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BarbarossaBckereiDESpider(WPStoreLocatorSpider):
    name = "barbarossa_bckerei_de"
    item_attributes = {
        "brand_wikidata": "Q807766",
        "brand": "Barbarossa Bäckerei",
    }
    allowed_domains = [
        "www.barbarossa-baeckerei.de",
    ]
    days = DAYS_DE
