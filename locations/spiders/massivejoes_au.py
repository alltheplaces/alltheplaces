from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MassivejoesAUSpider(WPStoreLocatorSpider):
    name = "massivejoes_au"
    item_attributes = {
        "brand": "MassiveJoes",
        "brand_wikidata": "Q117746887",
        "extras": Categories.SHOP_NUTRITION_SUPPLEMENTS.value,
    }
    allowed_domains = ["massivejoes.com"]
    days = DAYS_EN
