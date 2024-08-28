from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SanelNapaUSSpider(WPStoreLocatorSpider):
    name = "sanel_napa_us"
    item_attributes = {"brand_wikidata": "Q122564780", "brand": "Sanel NAPA", "extras": Categories.SHOP_CAR_PARTS.value}
    allowed_domains = [
        "sanelnapa.com",
    ]
    days = DAYS_EN
