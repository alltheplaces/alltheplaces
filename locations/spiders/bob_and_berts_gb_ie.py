from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BobAndBertsGBIESpider(WPStoreLocatorSpider):
    name = "bob_and_berts_gb_ie"
    item_attributes = {"brand_wikidata": "Q113494662", "brand": "Bob & Berts", "extras": Categories.CAFE.value}
    allowed_domains = [
        "bobandberts.co.uk",
    ]
    days = DAYS_EN
