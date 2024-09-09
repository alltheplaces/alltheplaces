from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PTerrysUSSpider(WPStoreLocatorSpider):
    name = "p_terrys_us"
    item_attributes = {"brand_wikidata": "Q19903521", "brand": "P. Terry's", "extras": Categories.FAST_FOOD.value}
    allowed_domains = [
        "pterrys.com",
    ]
    days = DAYS_EN
