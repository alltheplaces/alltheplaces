from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MrPriceIESpider(WPStoreLocatorSpider):
    name = "mr_price_ie"
    item_attributes = {
        "brand_wikidata": "Q113197454",
        "brand": "Mr. Price",
        "extras": Categories.SHOP_VARIETY_STORE.value,
    }
    allowed_domains = [
        "www.mrprice.ie",
    ]
    days = DAYS_EN
