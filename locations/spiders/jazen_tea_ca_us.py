from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class JazenTeaCAUSSpider(WPStoreLocatorSpider):
    name = "jazen_tea_ca_us"
    item_attributes = {"brand_wikidata": "Q114989479", "brand": "Jazen Tea", "extras": Categories.CAFE.value}
    allowed_domains = [
        "www.jazentea.com",
    ]
    days = DAYS_EN
