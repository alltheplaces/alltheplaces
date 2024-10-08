from locations.categories import Categories
from locations.hours import DAYS_SK
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class FarmfoodsSKSpider(WPStoreLocatorSpider):
    name = "farmfoods_sk"
    item_attributes = {
        "brand_wikidata": "Q116867227",
        "brand": "FARMFOODS",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }
    allowed_domains = [
        "predajne.farmfoods.sk",
    ]
    days = DAYS_SK
