from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ReformhausBacherDESpider(WPStoreLocatorSpider):
    name = "reformhaus_bacher_de"
    item_attributes = {
        "brand_wikidata": "Q19816424",
        "brand": "Reformhaus Bacher",
        "extras": Categories.SHOP_HEALTH_FOOD.value,
    }
    allowed_domains = [
        "www.reformhaus-bacher.de",
    ]
    days = DAYS_EN
