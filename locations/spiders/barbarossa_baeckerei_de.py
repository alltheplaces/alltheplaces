from locations.hours import DAYS_DE
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BarbarossaBaeckereiDESpider(WPStoreLocatorSpider):
    name = "barbarossa_baeckerei_de"
    item_attributes = {"brand": "Barbarossa Bäckerei", "brand_wikidata": "Q807766"}
    drop_attributes = {"name"}
    allowed_domains = ["www.barbarossa-baeckerei.de"]
    days = DAYS_DE
