from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CarpetCourtNZSpider(WPStoreLocatorSpider):
    name = "carpet_court_nz"
    item_attributes = {"brand": "Carpet Court", "brand_wikidata": "Q117156437", "extras": Categories.SHOP_CARPET.value}
    allowed_domains = ["carpetcourt.nz"]
    days = DAYS_EN
